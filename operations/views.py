from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django_tables2 import SingleTableView
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_GET,
)
from django.utils.http import url_has_allowed_host_and_scheme

from .lib.aamva import aamva_2020
import typing
from .forms import (
    CheckInForm,
    IncidentForm,
    InviteUserForm,
    ManageUserRoleForm,
    SupportRequestForm,
    AssetCategoryForm,
    AssetForm,
    AssetCheckoutForm,
    AssetAcceptForm,
    AssetCheckinForm,
    TimeEntryForm,
)
from .models import (
    Incident,
    CheckIn,
    IncidentOrganization,
    IncidentOrganizationUser,
    IncidentOrganizationInvitation,
    SupportRequest,
    IncidentLink,
    AssetCategory,
    Asset,
    AssetCheckout,
    TimeEntry,
)
from .tables import CheckInTable

from logging import getLogger

# URL name constants to avoid duplication
ORGANIZATION_LIST_URL = "operations:organization_list"
TIME_ENTRY_LIST_URL = "operations:time_entry_list"
DASHBOARD_URL = "operations:dashboard"
ORGANIZATION_DETAIL_URL = "operations:organization_detail"
ORGANIZATION_PUBLIC_PROFILE_URL = "operations:organization_public_profile"
INCIDENT_DETAIL_URL = "operations:incident_detail"
ASSET_DETAIL_URL = "operations:asset_detail"
CHECKIN_INDEX_URL = "operations:checkin_index"
CHECKIN_REPORT_URL = "operations:checkin_report"
SUPPORT_REQUESTS_LIST_URL = "operations:support_requests_list"
SUPPORT_REQUEST_DETAIL_URL = "operations:support_request_detail"
ASSET_LIST_URL = "operations:asset_list"
ASSET_CATEGORY_LIST_URL = "operations:asset_category_list"
TIME_ENTRY_DETAIL_URL = "operations:time_entry_detail"

# Error message constants
NO_ACCESS_ORGANIZATION_MSG = "You don't have access to this organization."

logger = getLogger(__name__)


def safe_redirect(request, fallback_url):
    """
    Safely redirect to HTTP_REFERER if it's safe, otherwise use fallback URL.
    Prevents open redirect vulnerabilities.
    """
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts=request.get_host(),
        require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect(fallback_url)


def get_accessible_incidents(user, current_organization=None):
    """Get incidents that the user has access to based on organization membership"""
    if not user.is_authenticated:
        return Incident.objects.none()

    # Superusers can see all incidents
    if user.is_superuser:
        if current_organization:
            return Incident.objects.filter(organization=current_organization)
        return Incident.objects.all()

    # Get incidents from organizations the user belongs to
    user_orgs = IncidentOrganizationUser.objects.filter(user=user).values_list(
        "organization", flat=True
    )

    if user_orgs:
        if current_organization:
            # Filter to only the current organization if user has access to it
            if current_organization.id in user_orgs:
                return Incident.objects.filter(organization=current_organization)
            else:
                # User doesn't have access to requested organization
                return Incident.objects.none()
        else:
            # Show incidents from all user's organizations
            return Incident.objects.filter(organization__in=user_orgs)

    # If user is not in any organization, only show incidents they own
    return Incident.objects.filter(owner=user)


def get_current_organization(request):
    """Get the current organization from session if set and user has access"""
    org_id = request.session.get("current_organization_id")
    if not org_id:
        return None

    try:
        organization = IncidentOrganization.objects.get(id=org_id)
        # Check if user has access to this organization
        if IncidentOrganizationUser.objects.filter(
            user=request.user, organization=organization
        ).exists():
            return organization
    except IncidentOrganization.DoesNotExist:
        pass

    # Clear invalid organization from session
    request.session.pop("current_organization_id", None)
    return None


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
@require_GET
def dashboard(request):
    """Main operations dashboard providing an overview of all operations activities"""
    context = {}

    # Get current organization from context processor (will be in template context)
    current_org_id = request.session.get("current_organization_id")
    current_organization = None
    if current_org_id:
        try:
            current_organization = IncidentOrganization.objects.get(id=current_org_id)
        except IncidentOrganization.DoesNotExist:
            request.session.pop("current_organization_id", None)

    # Get incidents user has access to, filtered by current organization if set
    all_incidents = get_accessible_incidents(request.user, current_organization).order_by(
        "-start_date"
    )
    active_incidents = all_incidents.filter(status="ACTIVE")

    # Overall statistics
    total_incidents = all_incidents.count()
    active_incidents_count = active_incidents.count()

    # Filter check-ins by current organization if set
    if current_organization:
        total_checkins_all_time = CheckIn.objects.filter(
            incident__organization=current_organization
        ).count()
        current_active_checkins = CheckIn.objects.filter(
            Check_Out=False, incident__status="ACTIVE", incident__organization=current_organization
        ).count()
        recent_checkins = (
            CheckIn.objects.select_related("incident", "user")
            .filter(incident__organization=current_organization)
            .order_by("-timestamp")[:10]
        )
    else:
        # Show data from all accessible incidents
        accessible_incident_ids = all_incidents.values_list("id", flat=True)
        total_checkins_all_time = CheckIn.objects.filter(
            incident__id__in=accessible_incident_ids
        ).count()
        current_active_checkins = CheckIn.objects.filter(
            Check_Out=False, incident__status="ACTIVE", incident__id__in=accessible_incident_ids
        ).count()
        recent_checkins = (
            CheckIn.objects.select_related("incident", "user")
            .filter(incident__id__in=accessible_incident_ids)
            .order_by("-timestamp")[:10]
        )

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
        if current_organization:
            # Check role in current organization
            try:
                user_role = IncidentOrganizationUser.objects.get(
                    user=request.user, organization=current_organization
                ).role
                can_create_incidents = user_role in ["ADMIN", "INCIDENT_MANAGER"]
            except IncidentOrganizationUser.DoesNotExist:
                can_create_incidents = False
        else:
            # Check if user has the required role in any organization
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
@require_GET
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
@require_http_methods(["GET", "POST"])
def new(request, incident_id):
    """Create a new check-in for a specific incident"""
    context = {}

    # Get the specific incident and verify user has write access
    incident = get_object_or_404(Incident, id=incident_id, status="ACTIVE")

    # Check if user has write access to this incident
    if not incident.has_write_access(request.user):
        messages.error(request, "You don't have permission to check-in to this incident.")
        return redirect(CHECKIN_INDEX_URL)

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
            return redirect(CHECKIN_INDEX_URL)
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
@require_POST
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
    return redirect(CHECKIN_REPORT_URL)


@login_required()
def _get_current_organization(request):
    """Helper to get current organization from session"""
    current_org_id = request.session.get("current_organization_id")
    if current_org_id:
        try:
            return IncidentOrganization.objects.get(id=current_org_id)
        except IncidentOrganization.DoesNotExist:
            request.session.pop("current_organization_id", None)
    return None


def _check_incident_creation_permission(user, current_organization):
    """Helper to check if user can create incidents and return default org"""
    if user.is_superuser:
        return True, current_organization

    # Check permission in current organization
    if current_organization:
        try:
            membership = IncidentOrganizationUser.objects.get(
                user=user, organization=current_organization
            )
            if membership.role in ["ADMIN", "INCIDENT_MANAGER"]:
                return True, current_organization
        except IncidentOrganizationUser.DoesNotExist:
            pass

    # Check if user has permission in any organization
    user_org_memberships = IncidentOrganizationUser.objects.filter(user=user)
    for membership in user_org_memberships:
        if membership.role in ["ADMIN", "INCIDENT_MANAGER"]:
            return True, membership.organization

    return False, None


@login_required()
@require_http_methods(["GET", "POST"])
def create_incident(request):
    """Create a new incident"""
    current_organization = _get_current_organization(request)
    can_create, default_org = _check_incident_creation_permission(request.user, current_organization)

    if not can_create:
        messages.error(request, "You don't have permission to create incidents.")
        return redirect(DASHBOARD_URL)

    if request.method == "POST":
        form = IncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.owner = request.user
            incident.created_by = request.user

            # Set organization based on current context or form selection
            if not incident.organization and default_org:
                incident.organization = default_org

            incident.save()

            messages.success(request, f"Incident '{incident.name}' has been created successfully!")
            return redirect(DASHBOARD_URL)
    else:
        form = IncidentForm()
        # If there's a default organization, pre-select it
        if default_org:
            form.initial["organization"] = default_org

    context = {
        "form": form,
        "page_title": "Create New Incident",
    }
    return render(request, "operations/incident/create.html", context)


@login_required()
@require_GET
def incident_detail(request, incident_id):
    """Display incident details including incident commander information"""
    incident = get_object_or_404(Incident, id=incident_id)

    # Check if user has read access to this incident
    if not incident.has_read_access(request.user):
        messages.error(request, "You don't have permission to view this incident.")
        return redirect(DASHBOARD_URL)

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
@require_GET
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
@require_GET
def organization_detail(request, org_id):
    """View organization details and manage members"""
    # Check if user belongs to this organization
    try:
        user_membership = IncidentOrganizationUser.objects.get(
            user=request.user, organization_id=org_id
        )
        organization = user_membership.organization
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, NO_ACCESS_ORGANIZATION_MSG)
        return redirect(ORGANIZATION_LIST_URL)

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
def _check_invitation_permission(user, org_id):
    """Helper to check if user can invite others to organization"""
    try:
        user_membership = IncidentOrganizationUser.objects.get(
            user=user, organization_id=org_id
        )
        if user_membership.role not in ["ADMIN", "INCIDENT_MANAGER"]:
            return False, None, "You don't have permission to invite users to this organization."
        return True, user_membership.organization, None
    except IncidentOrganizationUser.DoesNotExist:
        return False, None, NO_ACCESS_ORGANIZATION_MSG


def _validate_invitation_request(email, organization):
    """Helper to validate invitation request"""
    # Check if user already exists in organization
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        existing_membership = IncidentOrganizationUser.objects.filter(
            user=existing_user, organization=organization
        ).exists()
        if existing_membership:
            return False, f"User {email} is already a member of this organization."

    # Check if invitation already exists
    existing_invitation = IncidentOrganizationInvitation.objects.filter(
        invitee_identifier=email, organization=organization
    ).exists()
    if existing_invitation:
        return False, f"An invitation has already been sent to {email}."

    return True, None


@login_required()
@require_http_methods(["GET", "POST"])
def invite_user(request, org_id):
    """Invite a user to join an organization"""
    # Check if user has permission to invite
    has_permission, organization, error_msg = _check_invitation_permission(request.user, org_id)
    if not has_permission:
        messages.error(request, error_msg)
        if "access" in error_msg.lower():
            return redirect(ORGANIZATION_LIST_URL)
        return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)

    if request.method == "POST":
        form = InviteUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["invitee_identifier"]
            role = form.cleaned_data["role"]

            # Validate invitation request
            is_valid, validation_error = _validate_invitation_request(email, organization)
            if not is_valid:
                messages.error(request, validation_error)
                return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)

            # Create invitation
            IncidentOrganizationInvitation.objects.create(
                invitee_identifier=email,
                organization=organization,
                role=role,
                invited_by=request.user,
            )

            messages.success(request, f"Invitation sent to {email} successfully!")
            return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)
    else:
        form = InviteUserForm()

    context = {
        "form": form,
        "organization": organization,
        "page_title": f"Invite User to {organization.name}",
    }
    return render(request, "operations/organization/invite.html", context)


@login_required()
@require_http_methods(["GET", "POST"])
def manage_user_role(request, org_id, user_id):
    """Manage a user's role within an organization"""
    # Check if current user has permission to manage roles
    try:
        current_user_membership = IncidentOrganizationUser.objects.get(
            user=request.user, organization_id=org_id
        )
        if current_user_membership.role != "ADMIN":
            messages.error(request, "Only organization admins can manage user roles.")
            return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)
        organization = current_user_membership.organization
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, NO_ACCESS_ORGANIZATION_MSG)
        return redirect(ORGANIZATION_LIST_URL)

    # Get the user membership to manage
    try:
        user_membership = IncidentOrganizationUser.objects.get(
            organization=organization, user_id=user_id
        )
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, "User is not a member of this organization.")
        return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)

    # Prevent self-demotion
    if user_membership.user == request.user:
        messages.error(request, "You cannot change your own role.")
        return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)

    if request.method == "POST":
        form = ManageUserRoleForm(request.POST, instance=user_membership)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Updated role for {user_membership.user.get_full_name() or user_membership.user.username}",
            )
            return redirect(ORGANIZATION_DETAIL_URL, org_id=org_id)
    else:
        form = ManageUserRoleForm(instance=user_membership)

    context = {
        "form": form,
        "organization": organization,
        "user_membership": user_membership,
        "page_title": f"Manage Role for {user_membership.user.get_full_name() or user_membership.user.username}",
    }
    return render(request, "operations/organization/manage_role.html", context)


@login_required
@require_GET
def organization_public_profile(request, org_id):
    """Public profile view for an organization - for requesting support"""
    organization = get_object_or_404(IncidentOrganization, id=org_id)

    # Get recent incidents for this organization
    recent_incidents = Incident.objects.filter(organization=organization, status="ACTIVE").order_by(
        "-start_date"
    )[:5]

    # Check if user can request support (must be from different organization)
    can_request_support = False
    user_orgs = []
    if request.user.is_authenticated:
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        can_request_support = organization.id not in user_orgs and user_orgs.exists()

    context = {
        "organization": organization,
        "recent_incidents": recent_incidents,
        "can_request_support": can_request_support,
        "user_orgs": user_orgs,
    }
    return render(request, "operations/organization/public_profile.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def request_support(request, org_id):
    """Create a support request to an organization"""
    target_organization = get_object_or_404(IncidentOrganization, id=org_id)

    # Check user has organization membership
    user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
        "organization", flat=True
    )
    if not user_orgs.exists():
        messages.error(request, "You must be a member of an organization to request support.")
        return redirect(ORGANIZATION_PUBLIC_PROFILE_URL, org_id=org_id)

    # Prevent requesting support from own organization
    if target_organization.id in user_orgs:
        messages.error(request, "You cannot request support from your own organization.")
        return redirect(ORGANIZATION_PUBLIC_PROFILE_URL, org_id=org_id)

    if request.method == "POST":
        form = SupportRequestForm(request.POST, user=request.user)
        if form.is_valid():
            support_request = form.save(commit=False)
            support_request.requesting_organization_id = user_orgs.first()  # Use first org
            support_request.target_organization = target_organization
            support_request.requested_by = request.user
            support_request.save()

            messages.success(
                request,
                f"Support request sent to {target_organization.name}. "
                f"You will be notified when they respond.",
            )
            return redirect(ORGANIZATION_PUBLIC_PROFILE_URL, org_id=org_id)
    else:
        form = SupportRequestForm(user=request.user)

    context = {
        "form": form,
        "target_organization": target_organization,
        "page_title": f"Request Support from {target_organization.name}",
    }
    return render(request, "operations/support/request_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def request_support_for_incident(request, incident_id):
    """Create a support request for a specific incident"""
    incident = get_object_or_404(Incident, id=incident_id)

    # Check if user has access to this incident
    if not incident.has_read_access(request.user):
        messages.error(request, "You don't have permission to view this incident.")
        return redirect(DASHBOARD_URL)

    # Check user has organization membership
    user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
        "organization", flat=True
    )
    if not user_orgs.exists():
        messages.error(request, "You must be a member of an organization to request support.")
        return redirect(INCIDENT_DETAIL_URL, incident_id=incident_id)

    # Determine the requesting organization (current organization context or first org)
    current_org_id = request.session.get("current_organization_id")
    if current_org_id and current_org_id in user_orgs:
        requesting_organization = IncidentOrganization.objects.get(id=current_org_id)
    else:
        requesting_organization = IncidentOrganization.objects.get(id=user_orgs.first())

    # Get all organizations available for support requests
    # Exclude the requesting organization as an org cannot request support from itself
    available_orgs = IncidentOrganization.objects.exclude(id=requesting_organization.id)

    if request.method == "POST":
        form = SupportRequestForm(
            request.POST,
            user=request.user,
            requesting_organization=requesting_organization,
            current_incident=incident,
        )
        if form.is_valid():
            support_request = form.save(commit=False)

            # Set the requesting organization
            support_request.requesting_organization = requesting_organization

            support_request.related_incident = incident
            support_request.requested_by = request.user
            support_request.save()

            messages.success(
                request,
                f"Support request sent to {support_request.target_organization.name} for incident '{incident.name}'. "
                f"You will be notified when they respond.",
            )
            return redirect(INCIDENT_DETAIL_URL, incident_id=incident_id)
    else:
        # Pre-populate the form with incident information
        initial_data = {
            "title": f"Support Request for {incident.name}",
            "description": f"We need support for the {incident.get_incident_type_display().lower()} incident: {incident.name}",
            "related_incident": incident.id,
        }
        form = SupportRequestForm(
            user=request.user,
            requesting_organization=requesting_organization,
            current_incident=incident,
            initial=initial_data,
        )

    context = {
        "form": form,
        "incident": incident,
        "available_organizations": available_orgs,
        "page_title": f"Request Support for {incident.name}",
    }
    return render(request, "operations/support/request_form_incident.html", context)


@login_required
@require_GET
def support_requests_list(request):
    """List support requests for user's organizations"""
    user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
        "organization", flat=True
    )

    if not user_orgs.exists():
        messages.warning(
            request, "You must be a member of an organization to view support requests."
        )
        return redirect(DASHBOARD_URL)

    # Check if user has a current organization context
    current_org_id = request.session.get("current_organization_id")

    # If user has a current organization context and it's valid, filter by that organization
    if current_org_id and current_org_id in user_orgs:
        filter_orgs = [current_org_id]
        current_org = IncidentOrganization.objects.get(id=current_org_id)
        context_message = f"Showing support requests for {current_org.name}"
    else:
        # No specific organization context, show all user's organizations
        filter_orgs = user_orgs
        context_message = "Showing support requests for all your organizations"

    # Get incoming and outgoing support requests (exclude cancelled for normal view)
    incoming_requests = (
        SupportRequest.objects.filter(target_organization__in=filter_orgs)
        .exclude(status="CANCELLED")
        .select_related("requesting_organization", "related_incident")
        .order_by("-created_at")
    )

    outgoing_requests = (
        SupportRequest.objects.filter(requesting_organization__in=filter_orgs)
        .exclude(status="CANCELLED")
        .select_related("target_organization", "related_incident")
        .order_by("-created_at")
    )

    context = {
        "incoming_requests": incoming_requests,
        "outgoing_requests": outgoing_requests,
        "context_message": context_message,
    }
    return render(request, "operations/support/requests_list.html", context)


def _check_support_request_access(support_request, user_orgs):
    """Check if user has access to view the support request"""
    return (
        support_request.requesting_organization_id in user_orgs
        or support_request.target_organization_id in user_orgs
    )


def _get_support_request_permissions(support_request, user_orgs):
    """Calculate user permissions for the support request"""
    can_review = support_request.target_organization_id in user_orgs
    can_create_incident = can_review and support_request.can_create_incident
    can_cancel = (
        support_request.requesting_organization_id in user_orgs
        and support_request.status == "PENDING"
    )
    return can_review, can_create_incident, can_cancel


def _handle_support_request_cancel(support_request, request):
    """Handle cancelling a support request"""
    support_request.status = "CANCELLED"
    support_request.reviewed_by = request.user
    support_request.reviewed_at = timezone.now()
    support_request.response_notes = request.POST.get(
        "cancel_reason", "Request cancelled by requesting organization"
    )
    support_request.save()
    messages.info(request, "Support request has been cancelled.")


def _handle_support_request_approve(support_request, request):
    """Handle approving a support request"""
    support_request.status = "APPROVED"
    support_request.reviewed_by = request.user
    support_request.reviewed_at = timezone.now()
    support_request.response_notes = request.POST.get("response_notes", "")
    support_request.approved_resources = request.POST.get("approved_resources", "")
    support_request.save()
    messages.success(request, "Support request approved.")


def _handle_support_request_decline(support_request, request):
    """Handle declining a support request"""
    support_request.status = "DECLINED"
    support_request.reviewed_by = request.user
    support_request.reviewed_at = timezone.now()
    support_request.response_notes = request.POST.get("response_notes", "")
    support_request.save()
    messages.info(request, "Support request declined.")


def _create_incident_from_support_request(support_request, user):
    """Create a new incident based on support request"""
    new_incident = Incident.objects.create(
        name=f"Support for {support_request.related_incident.name}",
        incident_type=support_request.related_incident.incident_type,
        description=f"Supporting {support_request.requesting_organization.name} for {support_request.related_incident.name}",
        organization=support_request.target_organization,
        owner=user,
        incident_commander=user,
        start_date=support_request.requested_start_date,
        end_date=support_request.requested_end_date,
        location=support_request.related_incident.location,
        parent_incident=support_request.related_incident,
        support_request=support_request,
    )

    # Create incident link
    IncidentLink.objects.create(
        from_incident=new_incident,
        to_incident=support_request.related_incident,
        relationship_type="SUPPORTS",
        notes=f"Created from support request: {support_request.title}",
        created_by=user,
    )

    support_request.status = "FULFILLED"
    support_request.save()

    return new_incident


@login_required
@require_http_methods(["GET", "POST"])
def support_request_detail(request, request_id):
    """View and manage a specific support request"""
    support_request = get_object_or_404(SupportRequest, id=request_id)

    # Check access permissions
    user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
        "organization", flat=True
    )

    if not _check_support_request_access(support_request, user_orgs):
        messages.error(request, "You don't have access to this support request.")
        return redirect(SUPPORT_REQUESTS_LIST_URL)

    can_review, can_create_incident, can_cancel = _get_support_request_permissions(
        support_request, user_orgs
    )

    if request.method == "POST":
        action = request.POST.get("action")

        # Handle cancel action (requesting organization members only)
        if action == "cancel" and can_cancel:
            _handle_support_request_cancel(support_request, request)
            return redirect(SUPPORT_REQUEST_DETAIL_URL, request_id=support_request.id)

        # Handle review actions (target organization members only)
        elif can_review:
            if action == "approve":
                _handle_support_request_approve(support_request, request)
            elif action == "decline":
                _handle_support_request_decline(support_request, request)
            elif action == "create_incident" and can_create_incident:
                new_incident = _create_incident_from_support_request(support_request, request.user)
                messages.success(
                    request,
                    f"Created incident '{new_incident.name}' and linked it to the original incident.",
                )
                return redirect(INCIDENT_DETAIL_URL, incident_id=new_incident.id)

        return redirect(SUPPORT_REQUEST_DETAIL_URL, request_id=support_request.id)

    context = {
        "support_request": support_request,
        "can_review": can_review,
        "can_create_incident": can_create_incident,
        "can_cancel": can_cancel,
    }
    return render(request, "operations/support/request_detail.html", context)


@login_required
@require_POST
def switch_organization(request, org_id):
    """
    Switch the user's current active organization context.
    This affects which incidents and data they see in the interface.
    """
    try:
        organization = get_object_or_404(IncidentOrganization, id=org_id)

        # Verify user has access to this organization
        if not IncidentOrganizationUser.objects.filter(
            user=request.user, organization=organization
        ).exists():
            messages.error(request, "You don't have access to that organization.")
            return redirect(DASHBOARD_URL)

        # Set the current organization in session
        request.session["current_organization_id"] = org_id
        messages.success(request, f"Switched to {organization.name}")

    except IncidentOrganization.DoesNotExist:
        messages.error(request, "Organization not found.")

    # Safe redirect back to where they came from, or dashboard
    return safe_redirect(request, DASHBOARD_URL)


@login_required
@require_POST
def clear_organization(request):
    """
    Clear the current organization context, showing data from all organizations.
    """
    request.session.pop("current_organization_id", None)
    messages.success(
        request, "Cleared organization filter - now showing data from all your organizations."
    )

    # Safe redirect back to where they came from, or dashboard
    return safe_redirect(request, DASHBOARD_URL)


# Asset Management Views


@login_required
@require_GET
def asset_list(request):
    """
    List all assets accessible to the user.
    """
    current_organization = get_current_organization(request)
    user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
        "organization", flat=True
    )

    if current_organization:
        # Filter to current organization only
        if current_organization.id in user_orgs:
            assets = Asset.objects.filter(organization=current_organization)
        else:
            assets = Asset.objects.none()
            messages.error(request, NO_ACCESS_ORGANIZATION_MSG)
    else:
        # Show assets from all user's organizations
        assets = Asset.objects.filter(organization__in=user_orgs)

    assets = assets.select_related(
        "category", "organization", "current_holder", "current_incident"
    ).order_by("identifier")

    context = {
        "assets": assets,
        "current_organization": current_organization,
    }
    return render(request, "operations/assets/asset_list.html", context)


@login_required
@require_GET
def asset_detail(request, asset_id):
    """
    Display detailed information about an asset.
    """
    asset = get_object_or_404(Asset, id=asset_id)

    # Check if user has access to this asset
    try:
        IncidentOrganizationUser.objects.get(organization=asset.organization, user=request.user)
    except IncidentOrganizationUser.DoesNotExist:
        messages.error(request, "You don't have access to this asset.")
        return redirect(ASSET_LIST_URL)

    # Get checkout history
    checkouts = (
        asset.checkouts.all()
        .select_related("checked_out_by", "checked_out_to", "incident")
        .order_by("-checkout_time")
    )

    # Check if user can checkout this asset
    can_checkout = asset.can_user_checkout(request.user)

    # Check if user can manage this asset
    can_manage = asset.can_user_manage(request.user)

    # Get pending checkout for this user if any
    pending_checkout = asset.checkouts.filter(checked_out_to=request.user, status="PENDING").first()

    # Get active checkout for this user if any
    active_checkout = asset.checkouts.filter(checked_out_to=request.user, status="ACTIVE").first()

    context = {
        "asset": asset,
        "checkouts": checkouts,
        "can_checkout": can_checkout,
        "can_manage": can_manage,
        "pending_checkout": pending_checkout,
        "active_checkout": active_checkout,
    }
    return render(request, "operations/assets/asset_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def asset_create(request):
    """
    Create a new asset.
    """
    if request.method == "POST":
        form = AssetForm(request.POST, user=request.user)
        if form.is_valid():
            asset = form.save()
            messages.success(request, f"Asset {asset.identifier} created successfully.")
            return redirect(ASSET_DETAIL_URL, asset_id=asset.id)
    else:
        form = AssetForm(user=request.user)

    context = {"form": form, "title": "Create Asset"}
    return render(request, "operations/assets/asset_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def asset_edit(request, asset_id):
    """
    Edit an existing asset.
    """
    asset = get_object_or_404(Asset, id=asset_id)

    # Check if user can manage this asset
    if not asset.can_user_manage(request.user):
        messages.error(request, "You don't have permission to edit this asset.")
        return redirect(ASSET_DETAIL_URL, asset_id=asset.id)

    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset, user=request.user)
        if form.is_valid():
            asset = form.save()
            messages.success(request, f"Asset {asset.identifier} updated successfully.")
            return redirect(ASSET_DETAIL_URL, asset_id=asset.id)
    else:
        form = AssetForm(instance=asset, user=request.user)

    context = {"form": form, "asset": asset, "title": f"Edit Asset: {asset.identifier}"}
    return render(request, "operations/assets/asset_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def asset_checkout(request, asset_id):
    """
    Checkout an asset to another user.
    """
    asset = get_object_or_404(Asset, id=asset_id)

    # Check if user can checkout this asset
    if not asset.can_user_checkout(request.user) and not asset.can_user_manage(request.user):
        messages.error(request, "You don't have permission to checkout this asset.")
        return redirect(ASSET_DETAIL_URL, asset_id=asset.id)

    if not asset.is_available:
        messages.error(request, "This asset is not available for checkout.")
        return redirect(ASSET_DETAIL_URL, asset_id=asset.id)

    if request.method == "POST":
        form = AssetCheckoutForm(request.POST, user=request.user, asset=asset)
        if form.is_valid():
            checkout = form.save(commit=False)
            checkout.asset = asset
            checkout.checked_out_by = request.user
            checkout.save()

            messages.success(
                request,
                f"Asset {asset.identifier} checkout initiated. Waiting for {checkout.checked_out_to.get_full_name() or checkout.checked_out_to.username} to accept.",
            )
            return redirect(ASSET_DETAIL_URL, asset_id=asset.id)
    else:
        form = AssetCheckoutForm(user=request.user, asset=asset)

    context = {"form": form, "asset": asset, "title": f"Checkout Asset: {asset.identifier}"}
    return render(request, "operations/assets/asset_checkout_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def asset_accept_checkout(request, checkout_id):
    """
    Accept a pending asset checkout.
    """
    checkout = get_object_or_404(AssetCheckout, id=checkout_id)

    if not checkout.can_user_accept(request.user):
        messages.error(request, "You cannot accept this checkout.")
        return redirect(ASSET_DETAIL_URL, asset_id=checkout.asset.id)

    if request.method == "POST":
        form = AssetAcceptForm(request.POST)
        if form.is_valid():
            try:
                checkout.accept_checkout(
                    user=request.user,
                    condition_notes=form.cleaned_data.get("condition_notes", ""),
                    location=form.cleaned_data.get("location", ""),
                )
                messages.success(request, f"Asset {checkout.asset.identifier} checkout accepted.")
            except ValueError as e:
                messages.error(request, str(e))
            return redirect(ASSET_DETAIL_URL, asset_id=checkout.asset.id)
    else:
        form = AssetAcceptForm()

    context = {
        "form": form,
        "checkout": checkout,
        "title": f"Accept Checkout: {checkout.asset.identifier}",
    }
    return render(request, "operations/assets/asset_accept_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def asset_checkin(request, checkout_id):
    """
    Check in an asset that is currently checked out.
    """
    checkout = get_object_or_404(AssetCheckout, id=checkout_id)

    if not checkout.can_user_checkin(request.user):
        messages.error(request, "You cannot check in this asset.")
        return redirect(ASSET_DETAIL_URL, asset_id=checkout.asset.id)

    if request.method == "POST":
        form = AssetCheckinForm(request.POST)
        if form.is_valid():
            try:
                checkout.checkin_asset(
                    user=request.user,
                    condition_notes=form.cleaned_data.get("condition_notes", ""),
                    location=form.cleaned_data.get("location", ""),
                    issues=form.cleaned_data.get("issues_reported", ""),
                )
                messages.success(
                    request, f"Asset {checkout.asset.identifier} checked in successfully."
                )
            except ValueError as e:
                messages.error(request, str(e))
            return redirect(ASSET_DETAIL_URL, asset_id=checkout.asset.id)
    else:
        form = AssetCheckinForm()

    context = {
        "form": form,
        "checkout": checkout,
        "title": f"Check In Asset: {checkout.asset.identifier}",
    }
    return render(request, "operations/assets/asset_checkin_form.html", context)


@login_required
@require_POST
def asset_cancel_checkout(request, checkout_id):
    """
    Cancel a pending asset checkout.
    """
    checkout = get_object_or_404(AssetCheckout, id=checkout_id)

    if not checkout.can_user_cancel(request.user):
        messages.error(request, "You cannot cancel this checkout.")
        return redirect(ASSET_DETAIL_URL, asset_id=checkout.asset.id)

    try:
        checkout.cancel_checkout(request.user)
        messages.success(
            request, f"Checkout for asset {checkout.asset.identifier} has been cancelled."
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(ASSET_DETAIL_URL, asset_id=checkout.asset.id)


@login_required
@require_GET
def asset_category_list(request):
    """
    List all asset categories.
    """
    categories = AssetCategory.objects.all().order_by("name")

    context = {"categories": categories}
    return render(request, "operations/assets/category_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def asset_category_create(request):
    """
    Create a new asset category.
    """
    # Check if user has admin permissions in any organization
    user_admin_orgs = IncidentOrganizationUser.objects.filter(
        user=request.user, role="ADMIN"
    ).exists()

    if not user_admin_orgs and not request.user.is_superuser:
        messages.error(request, "You don't have permission to create asset categories.")
        return redirect(ASSET_CATEGORY_LIST_URL)

    if request.method == "POST":
        form = AssetCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Asset category '{category.name}' created successfully.")
            return redirect(ASSET_CATEGORY_LIST_URL)
    else:
        form = AssetCategoryForm()

    context = {"form": form, "title": "Create Asset Category"}
    return render(request, "operations/assets/category_form.html", context)


@login_required
@require_GET
def my_assets(request):
    """
    Show assets currently checked out to the user.
    """
    # Get active checkouts for this user
    active_checkouts = (
        AssetCheckout.objects.filter(checked_out_to=request.user, status="ACTIVE")
        .select_related("asset", "asset__category", "incident")
        .order_by("asset__identifier")
    )

    # Get pending checkouts for this user
    pending_checkouts = (
        AssetCheckout.objects.filter(checked_out_to=request.user, status="PENDING")
        .select_related("asset", "asset__category", "checked_out_by")
        .order_by("asset__identifier")
    )

    context = {
        "active_checkouts": active_checkouts,
        "pending_checkouts": pending_checkouts,
    }
    return render(request, "operations/assets/my_assets.html", context)


# ==================== Time Tracking Views ====================

@login_required
@require_GET
def time_entry_list(request):
    """List time entries for the current user"""
    current_org = get_current_organization(request)
    if not current_org:
        messages.error(request, "Please select an organization first.")
        return redirect(ORGANIZATION_LIST_URL)
    
    # Get time entries for current user and organization
    time_entries = TimeEntry.objects.filter(
        user=request.user,
        organization=current_org
    ).select_related('incident', 'organization').order_by('-date')
    
    context = {
        "time_entries": time_entries,
        "current_organization": current_org,
    }
    return render(request, "operations/time/time_entry_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def time_entry_create(request):
    """Create a new time entry"""
    current_org = get_current_organization(request)
    if not current_org:
        messages.error(request, "Please select an organization first.")
        return redirect(ORGANIZATION_LIST_URL)
    
    if request.method == "POST":
        form = TimeEntryForm(request.POST, user=request.user)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.user = request.user
            
            # Ensure the organization is one the user belongs to
            if time_entry.organization not in IncidentOrganization.objects.filter(users=request.user):
                messages.error(request, "You don't have permission to log time for that organization.")
                return redirect(TIME_ENTRY_LIST_URL)
            
            time_entry.save()
            messages.success(request, "Time entry created successfully.")
            return redirect(TIME_ENTRY_DETAIL_URL, entry_id=time_entry.id)
    else:
        form = TimeEntryForm(user=request.user, initial={'organization': current_org})
    
    context = {
        "form": form,
        "current_organization": current_org,
    }
    return render(request, "operations/time/time_entry_form.html", context)


@login_required
@require_GET
def time_entry_detail(request, entry_id):
    """View a specific time entry"""
    time_entry = get_object_or_404(TimeEntry, id=entry_id)
    
    # Check permissions - users can only view their own time entries
    if time_entry.user != request.user and not request.user.is_superuser:
        messages.error(request, "You don't have permission to view this time entry.")
        return redirect(TIME_ENTRY_LIST_URL)
    
    context = {
        "time_entry": time_entry,
    }
    return render(request, "operations/time/time_entry_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def time_entry_edit(request, entry_id):
    """Edit a time entry"""
    time_entry = get_object_or_404(TimeEntry, id=entry_id)
    
    # Check permissions - users can only edit their own time entries
    if time_entry.user != request.user and not request.user.is_superuser:
        messages.error(
            request, "You don't have permission to edit this time entry."
        )
        return redirect(TIME_ENTRY_LIST_URL)
    
    if request.method == "POST":
        form = TimeEntryForm(
            request.POST, instance=time_entry, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Time entry updated successfully.")
            return redirect(TIME_ENTRY_DETAIL_URL, entry_id=time_entry.id)
    else:
        form = TimeEntryForm(instance=time_entry, user=request.user)
    
    context = {
        "form": form,
        "time_entry": time_entry,
    }
    return render(request, "operations/time/time_entry_form.html", context)


@login_required
@require_POST
def time_entry_delete(request, entry_id):
    """Delete a time entry"""
    time_entry = get_object_or_404(TimeEntry, id=entry_id)
    
    # Check permissions - users can only delete their own time entries
    if time_entry.user != request.user and not request.user.is_superuser:
        messages.error(
            request, "You don't have permission to delete this time entry."
        )
        return redirect(TIME_ENTRY_LIST_URL)
    
    if request.method == "POST":
        time_entry.delete()
        messages.success(request, "Time entry deleted successfully.")
        return redirect(TIME_ENTRY_LIST_URL)
    
    context = {
        "time_entry": time_entry,
    }
    return render(request, "operations/time/time_entry_delete.html", context)
