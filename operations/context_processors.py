"""
Context processors for the operations app.
Provides organization switching context and incident context to all templates.
"""

from .models import IncidentOrganization, IncidentOrganizationUser, Incident


def organization_context(request):
    """
    Adds organization switching context and current incident context to all templates.
    Provides current organization, available organizations, and active incidents.
    """
    context = {
        "current_organization": None,
        "user_organizations": [],
        "can_switch_organizations": False,
        "current_incident": None,
        "active_incidents": [],
        "total_active_incidents": 0,
    }

    if not request.user.is_authenticated:
        return context

    # Get all organizations the user is a member of
    user_org_memberships = IncidentOrganizationUser.objects.filter(
        user=request.user
    ).select_related("organization")

    user_organizations = [membership.organization for membership in user_org_memberships]
    context["user_organizations"] = user_organizations
    context["can_switch_organizations"] = len(user_organizations) > 1

    # Determine current organization
    current_org_id = request.session.get("current_organization_id")

    if current_org_id:
        # Try to get the organization from session
        try:
            current_org = IncidentOrganization.objects.get(id=current_org_id)
            # Verify user still has access to this organization
            if current_org in user_organizations:
                context["current_organization"] = current_org
            else:
                # Remove invalid organization from session
                request.session.pop("current_organization_id", None)
                current_org_id = None
        except IncidentOrganization.DoesNotExist:
            # Remove invalid organization from session
            request.session.pop("current_organization_id", None)
            current_org_id = None

    # If no current organization set, default to the first available
    if not current_org_id and user_organizations:
        context["current_organization"] = user_organizations[0]
        # Don't automatically set in session - let user explicitly choose

    # Get incident context information
    if user_organizations:
        user_org_ids = [org.id for org in user_organizations]

        # Get active incidents from user's organizations
        if context["current_organization"]:
            # Filter by current organization
            active_incidents = Incident.objects.filter(
                organization=context["current_organization"], status="ACTIVE"
            ).order_by("-start_date")
        else:
            # Get from all user's organizations
            active_incidents = Incident.objects.filter(
                organization__id__in=user_org_ids, status="ACTIVE"
            ).order_by("-start_date")

        context["active_incidents"] = active_incidents[:5]  # Limit to 5 for footer
        context["total_active_incidents"] = active_incidents.count()

        # If there's only one active incident, make it the "current" incident
        if active_incidents.count() == 1:
            context["current_incident"] = active_incidents.first()

    return context
