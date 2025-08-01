from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django_tables2 import SingleTableView
from django.contrib import messages

from .lib.aamva import aamva_2020
import typing
from .forms import CheckInForm
from .models import Incident, CheckIn
from .tables import CheckInTable

from logging import getLogger

logger = getLogger(__name__)


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

    # Get all incidents (active and inactive) with stats
    all_incidents = Incident.objects.all().order_by("-start_date")
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

    context.update(
        {
            "active_incidents": active_incidents,
            "incident_stats": incident_stats,
            "recent_checkins": recent_checkins,
            "total_incidents": total_incidents,
            "active_incidents_count": active_incidents_count,
            "total_checkins_all_time": total_checkins_all_time,
            "current_active_checkins": current_active_checkins,
        }
    )

    return render(request, "operations/dashboard.html", context)


class report(SingleTableView):
    model = CheckIn
    table_class = CheckInTable
    template_name = "operations/checkin/report.html"

    def get_queryset(self):
        """Filter check-ins by incident if specified"""
        queryset = super().get_queryset()
        incident_id = self.request.GET.get("incident")
        if incident_id:
            queryset = queryset.filter(incident_id=incident_id)
        return queryset.select_related("incident", "user")

    def get_context_data(self, **kwargs):
        """Add incidents list and current incident to context"""
        context = super().get_context_data(**kwargs)
        context["incidents"] = Incident.objects.filter(status="ACTIVE").order_by("-start_date")

        incident_id = self.request.GET.get("incident")
        if incident_id:
            try:
                context["current_incident"] = Incident.objects.get(id=incident_id)
            except Incident.DoesNotExist:
                pass

        return context


@login_required()
def index(request):
    """Main check-in dashboard showing active incidents and recent check-ins"""
    context = {}

    # Get active incidents
    active_incidents = Incident.objects.filter(status="ACTIVE").order_by("-start_date")
    context["active_incidents"] = active_incidents

    # Get recent check-ins across all active incidents
    recent_checkins = (
        CheckIn.objects.filter(incident__status="ACTIVE")
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

    # Get the specific incident
    incident = get_object_or_404(Incident, id=incident_id, status="ACTIVE")
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
