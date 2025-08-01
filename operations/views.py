from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_tables2 import SingleTableView
from django.contrib import messages

from .lib.aamva import aamva_2020
import typing
from .forms import CheckInForm, IncidentForm, InviteUserForm, ManageUserRoleForm
from .models import (
    Incident,
    CheckIn,
    IncidentOrganizationUser,
    IncidentOrganizationInvitation,
)
from .tables import CheckInTable

from logging import getLogger

logger = getLogger(__name__)


def get_accessible_incidents(user):
    """Get incidents that the user has access to based on organization membership"""
    if not user.is_authenticated:
        return Incident.objects.none()

    # Superusers can see all incidents
    if user.is_superuser:
        return Incident.objects.all()

    # Get incidents from organizations the user belongs to
    user_orgs = IncidentOrganizationUser.objects.filter(user=user).values_list(
        "organization", flat=True
    )
    if user_orgs:
        return Incident.objects.filter(organization__in=user_orgs)

    # If user is not in any organization, only show incidents they own
    return Incident.objects.filter(owner=user)


def decode_aamva_fields(pdf417_data_txt: typing.List[str]) -> dict:
    """
    pdf417_data_txt is a list of text lines consisting of the full PDF-417 data from the drivers license barcode
    """

    results = {}

    header_only = aamva_2020.parse_header(pdf417_data_txt)
    body_results = aamva_2020.parse_pdf417_data(pdf417_data_txt)

    results["header"] = header_only
    results["body"] = body_results

    return results


@login_required()
def dashboard(request):
    """Main operations dashboard providing an overview of all operations activities"""
    context = {}

    # Get incidents user has access to
    all_incidents = get_accessible_incidents(request.user).order_by("-start_date")
    active_incidents = all_incidents.filter(status="ACTIVE")

    # Overall statistics
    total_incidents = all_incidents.count()
    active_incidents_count = active_incidents.count()
    total_checkins_all_time = CheckIn.objects.count()
    current_active_checkins = CheckIn.objects.filter(
        Check_Out=False, incident__status="ACTIVE"
    ).count()

    # Recent activity across all incidents
    recent_checkins = CheckIn.objects.select_related("incident", "user").order_by("-timestamp")[:10]

    # Incident statistics
    incident_stats = []
    for incident in all_incidents[:10]:  # Show top 10 most recent incidents
        stats = {
            "incident": incident,
            "total_checkins": incident.total_checkins,
            "active_checkins": incident.active_checkins,
            "is_active": incident.status == "ACTIVE",
        }
        incident_stats.append(stats)

    # Check if user can create incidents (must be in an organization with ADMIN or INCIDENT_MANAGER role)
    can_create_incidents = False
    if request.user.is_superuser:
        can_create_incidents = True
    else:
        user_roles = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "role", flat=True
        )
        can_create_incidents = any(role in ["ADMIN", "INCIDENT_MANAGER"] for role in user_roles)

    context.update(
        {
            "active_incidents": active_incidents,
            "incident_stats": incident_stats,
            "recent_checkins": recent_checkins,
            "total_incidents": total_incidents,
            "active_incidents_count": active_incidents_count,
            "total_checkins_all_time": total_checkins_all_time,
            "current_active_checkins": current_active_checkins,
            "can_create_incidents": can_create_incidents,
        }
    )

    return render(request, "operations/dashboard.html", context)


class report(SingleTableView):
    model = CheckIn
    table_class = CheckInTable
    template_name = "operations/checkin/report.html"

    def get_queryset(self):
        """Filter check-ins by incident if specified and user permissions"""
        queryset = super().get_queryset()

        # Filter by accessible incidents
        accessible_incidents = get_accessible_incidents(self.request.user)
        queryset = queryset.filter(incident__in=accessible_incidents)

        incident_id = self.request.GET.get("incident")
        if incident_id:
            queryset = queryset.filter(incident_id=incident_id)
        return queryset.select_related("incident", "user")

    def get_context_data(self, **kwargs):
        """Add incidents list and current incident to context"""
        context = super().get_context_data(**kwargs)

        # Only show incidents user has access to
        accessible_incidents = get_accessible_incidents(self.request.user)
        context["incidents"] = accessible_incidents.filter(status="ACTIVE").order_by("-start_date")

        incident_id = self.request.GET.get("incident")
        if incident_id:
            try:
                # Make sure user has access to this incident
                context["current_incident"] = accessible_incidents.get(id=incident_id)
            except Incident.DoesNotExist:
                pass

        return context


@login_required()
def index(request):
    """Main check-in dashboard showing active incidents and recent check-ins"""
    context = {}

    # Get active incidents user has access to
    accessible_incidents = get_accessible_incidents(request.user)
    active_incidents = accessible_incidents.filter(status="ACTIVE").order_by("-start_date")
    context["active_incidents"] = active_incidents

    # Get recent check-ins across all accessible active incidents
    recent_checkins = (
        CheckIn.objects.filter(incident__in=active_incidents)
        .select_related("incident", "user")
        .order_by("-timestamp")[:10]
    )
    context["recent_checkins"] = recent_checkins

    # Get stats for active incidents
    incident_stats = []
    for incident in active_incidents:
        stats = {
            "incident": incident,
            "total_checkins": incident.total_checkins,
            "active_checkins": incident.active_checkins,
        }
        incident_stats.append(stats)
    context["incident_stats"] = incident_stats

    return render(request, "operations/checkin/home.html", context)


@login_required()
def new(request, incident_id):
    """Create a new check-in for a specific incident"""
    context = {}

    # Get the specific incident and verify user has write access
    incident = get_object_or_404(Incident, id=incident_id, status="ACTIVE")

    # Check if user has write access to this incident
    if not incident.has_write_access(request.user):
        messages.error(request, "You don't have permission to check-in to this incident.")
        return redirect("operations:checkin_index")

    context["incident"] = incident

    # Pass incident to form constructor
    context["form"] = CheckInForm(incident=incident)

    if request.method == "POST":
        details = CheckInForm(request.POST, incident=incident)
        if details.is_valid():
            checkin = _process_valid_checkin_form(details, incident)
            messages.success(
                request,
                f"Check-in successful for {checkin.first_name} {checkin.last_name} "
                f"into {incident.name}",
            )
            return redirect("operations:checkin_index")
        else:
            context["form"] = details  # Pass the form with errors back to the template

    return render(request, "operations/checkin/new.html", context)


def _process_valid_checkin_form(details, incident):
    """Process valid check-in form data"""
    checkin = details.save(commit=False)

    # Set the incident for this check-in
    checkin.incident = incident

    id_card_results = decode_aamva_fields(
        [x for x in details.cleaned_data["dl_data"].splitlines() if x != ""]
    )

    # Get names from driver's license
    dl_first_name = id_card_results["body"].get("DAC", {}).get("value", "")
    dl_last_name = id_card_results["body"].get("DCS", {}).get("value", "")

    _set_checkin_names(checkin, dl_first_name, dl_last_name)

    logger.info(
        f"Processing check-in for {checkin.first_name} {checkin.last_name} into incident {checkin.incident.name}"
    )
    checkin.save()
    return checkin


def _set_checkin_names(checkin, dl_first_name, dl_last_name):
    """Set first and last names for check-in based on user selection and driver's license"""
    if not checkin.user:
        # No user selected - use names from driver's license
        checkin.first_name = dl_first_name
        checkin.last_name = dl_last_name
    else:
        # User is selected - use form names or fall back to DL/user names
        if not checkin.first_name:
            checkin.first_name = dl_first_name or checkin.user.first_name
        if not checkin.last_name:
            checkin.last_name = dl_last_name or checkin.user.last_name


@login_required()
def checkout(request, pk):
    """
    Handle checkout functionality for a specific CheckIn record.
    """
    checkin = get_object_or_404(CheckIn, pk=pk)

    # Check if already checked out
    if checkin.Check_Out:
        messages.warning(
            request, f"{checkin.first_name} {checkin.last_name} is already checked out."
        )
    else:
        # Mark as checked out and set checkout time
        from django.utils import timezone

        checkin.Check_Out = True
        checkin.checkout_time = timezone.now()
        checkin.save()

        messages.success(
            request,
            f"{checkin.first_name} {checkin.last_name} has been checked out of {checkin.incident.name} successfully.",
        )

    # Redirect back to the report page
    return redirect("operations:checkin_report")


@login_required()
def create_incident(request):
    """Create a new incident"""
    # Check if user has permission to create incidents (ADMIN or INCIDENT_MANAGER role)
    can_create = False
    user_org = None

    if request.user.is_superuser:
        can_create = True
    else:
        user_org_memberships = IncidentOrganizationUser.objects.filter(user=request.user)
        for membership in user_org_memberships:
            if membership.role in ["ADMIN", "INCIDENT_MANAGER"]:
                can_create = True
                user_org = membership.organization
                break

    if not can_create:
        messages.error(request, "You don't have permission to create incidents.")
        return redirect("operations:dashboard")

    if request.method == "POST":
        form = IncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.owner = request.user
            incident.created_by = request.user

            # Set organization based on user's primary organization or form selection
            if not incident.organization and user_org:
                incident.organization = user_org

            incident.save()

            messages.success(request, f"Incident '{incident.name}' has been created successfully!")
            return redirect("operations:dashboard")
    else:
        form = IncidentForm()
        # If user has a default organization, pre-select it
        if user_org:
            form.initial["organization"] = user_org

    context = {
        "form": form,
        "page_title": "Create New Incident",
    }
    return render(request, "operations/incident/create.html", context)


@login_required()
def incident_detail(request, incident_id):
    """Display incident details including incident commander information"""
    incident = get_object_or_404(Incident, id=incident_id)

    # Check if user has read access to this incident
    if not incident.has_read_access(request.user):
        messages.error(request, "You don't have permission to view this incident.")
        return redirect("operations:dashboard")

    # Get recent check-ins for this incident
    recent_checkins = (
        CheckIn.objects.filter(incident=incident).select_related("user").order_by("-timestamp")[:10]
    )

    context = {
        "incident": incident,
        "recent_checkins": recent_checkins,
        "total_checkins": incident.total_checkins,
        "active_checkins": incident.active_checkins,
        "can_edit": incident.has_admin_access(request.user),
        "can_checkin": incident.has_write_access(request.user),
    }
    return render(request, "operations/incident/detail.html", context)


@login_required()
def organization_list(request):
    """List organizations user belongs to"""
    user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).select_related(
        "organization"
    )

    context = {
        "user_organizations": user_orgs,
        "page_title": "My Organizations",
    }
    return render(request, "operations/organization/list.html", context)


@login_required()
def organization_detail(request, org_id):
    """View organization details and manage members"""
    # Check if user belongs to this organization
    try:
        user_membership = IncidentOrganizationUser.objects.get(
            user=request.user, organization_id=org_id
        )
        organization = user_membership.organization
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, "You don't have access to this organization.")
        return redirect("operations:organization_list")

    # Get all members of this organization
    members = IncidentOrganizationUser.objects.filter(organization=organization).select_related(
        "user"
    )

    # Get pending invitations if user is admin
    pending_invitations = []
    if user_membership.role in ["ADMIN", "INCIDENT_MANAGER"]:
        pending_invitations = IncidentOrganizationInvitation.objects.filter(
            organization=organization
        )

    context = {
        "organization": organization,
        "user_membership": user_membership,
        "members": members,
        "pending_invitations": pending_invitations,
        "can_manage": user_membership.role in ["ADMIN", "INCIDENT_MANAGER"],
        "page_title": f"{organization.name} - Organization Details",
    }
    return render(request, "operations/organization/detail.html", context)


@login_required()
def invite_user(request, org_id):
    """Invite a user to join an organization"""
    # Check if user has permission to invite
    try:
        user_membership = IncidentOrganizationUser.objects.get(
            user=request.user, organization_id=org_id
        )
        if user_membership.role not in ["ADMIN", "INCIDENT_MANAGER"]:
            messages.error(
                request, "You don't have permission to invite users to this organization."
            )
            return redirect("operations:organization_detail", org_id=org_id)
        organization = user_membership.organization
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, "You don't have access to this organization.")
        return redirect("operations:organization_list")

    if request.method == "POST":
        form = InviteUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["invitee_identifier"]
            role = form.cleaned_data["role"]

            # Check if user already exists in organization
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                existing_membership = IncidentOrganizationUser.objects.filter(
                    user=existing_user, organization=organization
                ).exists()
                if existing_membership:
                    messages.error(
                        request, f"User {email} is already a member of this organization."
                    )
                    return redirect("operations:organization_detail", org_id=org_id)

            # Check if invitation already exists
            existing_invitation = IncidentOrganizationInvitation.objects.filter(
                invitee_identifier=email, organization=organization
            ).exists()
            if existing_invitation:
                messages.error(request, f"An invitation has already been sent to {email}.")
                return redirect("operations:organization_detail", org_id=org_id)

            # Create invitation
            IncidentOrganizationInvitation.objects.create(
                invitee_identifier=email,
                organization=organization,
                role=role,
                invited_by=request.user,
            )

            messages.success(request, f"Invitation sent to {email} successfully!")
            return redirect("operations:organization_detail", org_id=org_id)
    else:
        form = InviteUserForm()

    context = {
        "form": form,
        "organization": organization,
        "page_title": f"Invite User to {organization.name}",
    }
    return render(request, "operations/organization/invite.html", context)


@login_required()
def manage_user_role(request, org_id, user_id):
    """Manage a user's role within an organization"""
    # Check if current user has permission to manage roles
    try:
        current_user_membership = IncidentOrganizationUser.objects.get(
            user=request.user, organization_id=org_id
        )
        if current_user_membership.role != "ADMIN":
            messages.error(request, "Only organization admins can manage user roles.")
            return redirect("operations:organization_detail", org_id=org_id)
        organization = current_user_membership.organization
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, "You don't have access to this organization.")
        return redirect("operations:organization_list")

    # Get the user membership to manage
    try:
        user_membership = IncidentOrganizationUser.objects.get(
            organization=organization, user_id=user_id
        )
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, "User is not a member of this organization.")
        return redirect("operations:organization_detail", org_id=org_id)

    # Prevent self-demotion
    if user_membership.user == request.user:
        messages.error(request, "You cannot change your own role.")
        return redirect("operations:organization_detail", org_id=org_id)

    if request.method == "POST":
        form = ManageUserRoleForm(request.POST, instance=user_membership)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Updated role for {user_membership.user.get_full_name() or user_membership.user.username}",
            )
            return redirect("operations:organization_detail", org_id=org_id)
    else:
        form = ManageUserRoleForm(instance=user_membership)

    context = {
        "form": form,
        "organization": organization,
        "user_membership": user_membership,
        "page_title": f"Manage Role for {user_membership.user.get_full_name() or user_membership.user.username}",
    }
    return render(request, "operations/organization/manage_role.html", context)
