from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import CheckIn
from logging import getLogger
import re

logger = getLogger(__name__)


class CheckInForm(ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="-- No user account (manual entry) --",
        help_text="Select a user account if the person being checked in has one",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    dl_data = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "cols": 40}),
        label="Driver's License Data",
        help_text="Paste the full text data from the back of your driver's license here.",
    )
    expense_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "cols": 40}),
        initial="n/a",
        required=True,
        help_text="Explain any large expenses or unusual mileage.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order users by first name, last name for better UX
        self.fields["user"].queryset = User.objects.all().order_by(
            "first_name", "last_name", "username"
        )
        # Custom display for users showing full name if available
        self.fields["user"].label_from_instance = self.user_label_from_instance

    def user_label_from_instance(self, user):
        """Show user's full name and username for better identification"""
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name} ({user.username})"
        elif user.first_name:
            return f"{user.first_name} ({user.username})"
        elif user.last_name:
            return f"{user.last_name} ({user.username})"
        else:
            return user.username

    class Meta:
        model = CheckIn
        fields = [
            "user",
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

        self._auto_populate_user_data()
        self._validate_numeric_fields()
        self._validate_roster_id()
        self._validate_driver_license_data()

        return self.cleaned_data

    def _auto_populate_user_data(self):
        """Auto-populate data from selected user's profile"""
        selected_user = self.cleaned_data.get("user")
        if not selected_user:
            return

        # Auto-populate roster ID if not provided and user has one saved
        if not self.cleaned_data.get("roster_id") and hasattr(selected_user, "profile"):
            profile = selected_user.profile
            if profile.roster_id:
                self.cleaned_data["roster_id"] = profile.roster_id
                logger.info(
                    f"Auto-populated roster ID {profile.roster_id} for user {selected_user.username}"
                )

        # Auto-populate names if not already set
        if not self.cleaned_data.get("first_name") and not self.cleaned_data.get("last_name"):
            if selected_user.first_name:
                self.cleaned_data["first_name"] = selected_user.first_name
            if selected_user.last_name:
                self.cleaned_data["last_name"] = selected_user.last_name

    def _validate_numeric_fields(self):
        """Validate that numeric expense fields are not negative"""
        if self.cleaned_data.get("mileage", 0) < 0:
            self.add_error("mileage", "Mileage cannot be negative")
            logger.warning("Mileage cannot be negative")
        if self.cleaned_data.get("food_expenses", 0) < 0:
            self.add_error("food_expenses", "Food expenses cannot be negative")
            logger.warning("Food expenses cannot be negative")
        if self.cleaned_data.get("other_expenses", 0) < 0:
            self.add_error("other_expenses", "Other expenses cannot be negative")
            logger.warning("Other expenses cannot be negative")

    def _validate_roster_id(self):
        """Validate roster ID format"""
        roster_id = self.cleaned_data.get("roster_id", "").upper()
        self.cleaned_data["roster_id"] = roster_id
        if not re.match(r"^[A-Za-z]{3}\d{4}$", str(roster_id)):
            self.add_error(
                "roster_id",
                "Roster ID must be 3 letters followed by 4 digits (e.g., ABC1234)",
            )
            logger.warning("Invalid roster_id format")

    def _validate_driver_license_data(self):
        """Validate driver's license data format"""
        dl_data = self.cleaned_data.get("dl_data", "")

        # Check AAMVA format
        if not self._is_valid_aamva_format(dl_data):
            self.add_error(
                "dl_data",
                "Driver's License data does not appear to be in AAMVA format.",
            )
            logger.warning("dl_data does not conform to AAMVA standard")

        # Check that the last line starts with "Z" and is at least 3 characters long
        if not self._is_valid_last_line(dl_data):
            self.add_error(
                "dl_data",
                "The last line of the data must start with 'Z' and be at least 3 characters long.",
            )
            logger.warning("Last line of dl_data does not start with 'Z' or is too short")

    def _is_valid_aamva_format(self, dl_data):
        """Check if driver's license data starts with valid AAMVA headers"""
        return dl_data.startswith("@") or dl_data.startswith("ANSI ") or dl_data.startswith("AAMVA")

    def _is_valid_last_line(self, dl_data):
        """Check if the last line of DL data is valid"""
        lines = [line.strip() for line in dl_data.splitlines() if line.strip()]
        if not lines:
            return False
        last_line = lines[-1]
        return last_line.startswith("Z") and len(last_line) >= 3
