from django import forms
from django.forms import ModelForm
from .models import CheckIn
from logging import getLogger
import re

logger = getLogger(__name__)


class CheckInForm(ModelForm):
    dl_data = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "cols": 40}),
        label="Driver's License Data",
        help_text="Paste the full text data from the back of your driver's license here.",
    )
    expense_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "cols": 40}),
        # label="Expense Notes2",
        initial="n/a",
        required=True,
        help_text="Explain any large expenses or unusual mileage.",
    )

    class Meta:
        model = CheckIn
        fields = [
            "roster_id",
            "mileage",
            "food_expenses",
            "other_expenses",
            "expense_notes",
            "dl_data",
        ]

    def clean(self):
        super(CheckInForm, self).clean()
        logger.warning("Cleaning checkin form data")
        logger.warning(f"Cleaned data: {self.cleaned_data}")

        if self.cleaned_data.get("mileage", 0) < 0:
            self.add_error("mileage", "Mileage cannot be negative")
            logger.warning("Mileage cannot be negative")
        if self.cleaned_data.get("food_expenses", 0) < 0:
            self.add_error("food_expenses", "Food expenses cannot be negative")
            logger.warning("Food expenses cannot be negative")
        if self.cleaned_data.get("other_expenses", 0) < 0:
            self.add_error("other_expenses", "Other expenses cannot be negative")
            logger.warning("Other expenses cannot be negative")

        roster_id = self.cleaned_data.get("roster_id", "").upper()
        self.cleaned_data["roster_id"] = roster_id
        if not re.match(r"^[A-Za-z]{3}\d{4}$", str(roster_id)):
            self.add_error(
                "roster_id", "Roster ID must be 3 letters followed by 4 digits (e.g., ABC1234)"
            )
            logger.warning("Invalid roster_id format")

        dl_data = self.cleaned_data.get("dl_data", "")
        # AAMVA standard PDF417 barcode data typically starts with "@", "ANSI ", or "AAMVA"
        if not (
            dl_data.startswith("@") or dl_data.startswith("ANSI ") or dl_data.startswith("AAMVA")
        ):
            self.add_error(
                "dl_data", "Driver's License data does not appear to be in AAMVA format."
            )
            logger.warning("dl_data does not conform to AAMVA standard")

        # Check that the last string starts with "Z" and is at least 3 characters long
        lines = [line.strip() for line in dl_data.splitlines() if line.strip()]
        if lines:
            last_line = lines[-1]
            if not (last_line.startswith("Z") and len(last_line) >= 3):
                self.add_error(
                    "dl_data",
                    "The last line of the data must start with 'Z' and be at least 3 characters long.",
                )
                logger.warning("Last line of dl_data does not start with 'Z' or is too short")

        return self.cleaned_data
