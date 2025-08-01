from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django_tables2 import SingleTableView
from django.contrib import messages

from .lib.aamva import aamva_2020
import typing
from .forms import CheckInForm
from .models import CheckIn
from .tables import CheckInTable

from logging import getLogger

logger = getLogger(__name__)


def decode_aamva_fields(pdf417_data_txt: typing.List[str]) -> dict:
    """
    pdf417_data_txt is a list of text lines consisting of the full PDF-417 data from the drivers license barcode
    """

    results = dict()

    header_only = aamva_2020.parse_header(pdf417_data_txt)
    body_results = aamva_2020.parse_pdf417_data(pdf417_data_txt)

    results["header"] = header_only
    results["body"] = body_results

    return results


class report(SingleTableView):
    model = CheckIn
    table_class = CheckInTable
    template_name = "checkin/report.html"


@login_required()
def index(request):
    context = {}

    return render(request, "checkin/home.html", context)


@login_required()
def new(request):
    context = {}
    context["form"] = CheckInForm()

    if request.method == "POST":
        details = CheckInForm(request.POST)
        if details.is_valid():
            # Process the valid form data
            checkin = details.save(commit=False)

            id_card_results = decode_aamva_fields(
                [x for x in details.cleaned_data["dl_data"].splitlines() if x != ""]
            )

            # Get names from driver's license
            dl_first_name = id_card_results["body"].get("DAC", {}).get("value", "")
            dl_last_name = id_card_results["body"].get("DCS", {}).get("value", "")

            # If no user is selected, use names from driver's license
            # If user is selected, keep the names that may have been auto-populated from user
            if not checkin.user:
                checkin.first_name = dl_first_name
                checkin.last_name = dl_last_name
            else:
                # User is selected - keep the names from form (may be auto-populated from user)
                # But if form names are empty, fall back to driver's license names
                if not checkin.first_name:
                    checkin.first_name = dl_first_name or checkin.user.first_name
                if not checkin.last_name:
                    checkin.last_name = dl_last_name or checkin.user.last_name

            logger.warning("Here")
            checkin.save()
            return render(request, "checkin/new.html", context)

        else:
            context["form"] = details  # Pass the form with errors back to the template

    return render(request, "checkin/new.html", context)


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
            f"{checkin.first_name} {checkin.last_name} has been checked out successfully.",
        )

    # Redirect back to the report page
    return redirect("checkin:report")
