from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import CheckIn, UserProfile
from logging import getLogger
import re

logger = getLogger(__name__)


class UserProfileForm(ModelForm):
    """
    Form for users to manage their profile information including roster ID
    """

    class Meta:
        model = UserProfile
        fields = ["roster_id"]
        widgets = {
            "roster_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "DOE1234", "maxlength": 7}
            )
        }

    def clean_roster_id(self):
        """Validate roster ID format"""
        roster_id = self.cleaned_data.get("roster_id", "").upper()
        if roster_id and not re.match(r"^[A-Za-z]{3}\d{4}$", roster_id):
            raise forms.ValidationError(
                "Roster ID must be 3 letters followed by 4 digits (e.g., ABC1234)"
            )
        return roster_id


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

        # If a user is selected, auto-populate data from their profile
        selected_user = self.cleaned_data.get("user")
        if selected_user:
            # Auto-populate roster ID if not provided and user has one saved
            if not self.cleaned_data.get("roster_id") and hasattr(selected_user, "checkin_profile"):
                profile = selected_user.checkin_profile
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
                "roster_id",
                "Roster ID must be 3 letters followed by 4 digits (e.g., ABC1234)",
            )
            logger.warning("Invalid roster_id format")

        dl_data = self.cleaned_data.get("dl_data", "")
        # AAMVA standard PDF417 barcode data typically starts with "@", "ANSI ", or "AAMVA"
        if not (
            dl_data.startswith("@") or dl_data.startswith("ANSI ") or dl_data.startswith("AAMVA")
        ):
            self.add_error(
                "dl_data",
                "Driver's License data does not appear to be in AAMVA format.",
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
