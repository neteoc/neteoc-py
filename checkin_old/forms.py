from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import CheckIn, UserProfile, Address
from logging import getLogger
import re

logger = getLogger(__name__)


class AddressForm(ModelForm):
    """
    Form for handling normalized address data
    """

    class Meta:
        model = Address
        fields = ["street_1", "street_2", "city", "state", "zip_code"]
        widgets = {
            "street_1": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "123 Main Street"}
            ),
            "street_2": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Apt 2B, Suite 100 (optional)"}
            ),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            "state": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "CA", "maxlength": 2}
            ),
            "zip_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "12345 or 12345-6789",
                    "maxlength": 10,
                }
            ),
        }

    def clean_state(self):
        """Validate state format"""
        state = self.cleaned_data.get("state", "").upper()
        if state and len(state) != 2:
            raise forms.ValidationError("State must be a 2-letter abbreviation (e.g., CA, NY)")
        return state

    def clean_zip_code(self):
        """Validate ZIP code format"""
        zip_code = self.cleaned_data.get("zip_code", "")
        if zip_code and not re.match(r"^\d{5}(-\d{4})?$", zip_code):
            raise forms.ValidationError("ZIP code must be in format 12345 or 12345-6789")
        return zip_code


class UserProfileForm(forms.Form):
    """
    Form for users to manage their profile information including roster ID and address
    """

    # UserProfile fields
    roster_id = forms.CharField(
        max_length=7,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "DOE1234", "maxlength": 7}
        ),
        help_text="Your default roster ID (e.g., DOE1234)",
    )
    drivers_license_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "DL123456789", "maxlength": 20}
        ),
        help_text="Your driver's license ID number",
    )

    # Address fields
    street_1 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "123 Main Street"}),
        help_text="Street address line 1",
    )
    street_2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Apt 2B, Suite 100 (optional)"}
        ),
        help_text="Street address line 2 (optional)",
    )
    city = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
        help_text="City name",
    )
    state = forms.CharField(
        max_length=2,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "CA", "maxlength": 2}
        ),
        help_text="State abbreviation (e.g., CA, NY)",
    )
    zip_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "12345 or 12345-6789", "maxlength": 10}
        ),
        help_text="ZIP code",
    )

    # Optional coordinate fields for manual entry
    latitude = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "40.7128", "step": "any"}
        ),
        help_text="Latitude (optional, for precise location)",
    )
    longitude = forms.DecimalField(
        max_digits=10,
        decimal_places=7,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "-74.0060", "step": "any"}
        ),
        help_text="Longitude (optional, for precise location)",
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)

        # Pre-populate fields if instance exists
        if self.instance:
            self.fields["roster_id"].initial = self.instance.roster_id
            self.fields["drivers_license_id"].initial = self.instance.drivers_license_id

            # Pre-populate address fields if address exists
            if self.instance.address:
                self.fields["street_1"].initial = self.instance.address.street_1
                self.fields["street_2"].initial = self.instance.address.street_2
                self.fields["city"].initial = self.instance.address.city
                self.fields["state"].initial = self.instance.address.state
                self.fields["zip_code"].initial = self.instance.address.zip_code

                # Pre-populate coordinates if available
                if self.instance.address.location:
                    self.fields["latitude"].initial = self.instance.address.latitude
                    self.fields["longitude"].initial = self.instance.address.longitude

    def clean_roster_id(self):
        """Validate roster ID format"""
        roster_id = self.cleaned_data.get("roster_id", "").upper()
        if roster_id and not re.match(r"^[A-Za-z]{3}\d{4}$", roster_id):
            raise forms.ValidationError(
                "Roster ID must be 3 letters followed by 4 digits (e.g., ABC1234)"
            )
        return roster_id

    def clean_state(self):
        """Validate state format"""
        state = self.cleaned_data.get("state", "").upper()
        if state and len(state) != 2:
            raise forms.ValidationError("State must be a 2-letter abbreviation (e.g., CA, NY)")
        return state

    def clean_zip_code(self):
        """Validate ZIP code format"""
        zip_code = self.cleaned_data.get("zip_code", "")
        if zip_code and not re.match(r"^\d{5}(-\d{4})?$", zip_code):
            raise forms.ValidationError("ZIP code must be in format 12345 or 12345-6789")
        return zip_code

    def save(self, user):
        """Save the form data to UserProfile and Address models"""
        # Get or create the user profile
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        # Update UserProfile fields
        user_profile.roster_id = self.cleaned_data.get("roster_id")
        user_profile.drivers_license_id = self.cleaned_data.get("drivers_license_id")

        # Handle address data
        address_data = {
            "street_1": self.cleaned_data.get("street_1"),
            "street_2": self.cleaned_data.get("street_2"),
            "city": self.cleaned_data.get("city"),
            "state": self.cleaned_data.get("state"),
            "zip_code": self.cleaned_data.get("zip_code"),
        }

        # Get coordinate data
        latitude = self.cleaned_data.get("latitude")
        longitude = self.cleaned_data.get("longitude")

        # Only create/update address if at least street_1, city, state, and zip_code are provided
        if (
            address_data["street_1"]
            and address_data["city"]
            and address_data["state"]
            and address_data["zip_code"]
        ):
            if user_profile.address:
                # Update existing address
                address = user_profile.address
                for field, value in address_data.items():
                    setattr(address, field, value)

                # Update coordinates if provided
                if latitude is not None and longitude is not None:
                    address.set_coordinates(longitude, latitude)
                    address.location_accuracy = "EXACT"
                elif not address.location:
                    # Clear coordinates if none provided and none exist
                    address.location = None
                    address.location_accuracy = None

                address.save()
            else:
                # Create new address
                address = Address.objects.create(**address_data)

                # Set coordinates if provided
                if latitude is not None and longitude is not None:
                    address.set_coordinates(longitude, latitude)
                    address.location_accuracy = "EXACT"
                    address.save()

                user_profile.address = address
        elif not any(address_data.values()):
            # If all address fields are empty, remove the address reference
            user_profile.address = None

        user_profile.save()
        return user_profile


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
