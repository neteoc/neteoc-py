from django import forms
from django.forms import ModelForm
from .models import UserProfile, Address, Contact
import re


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
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        self._save_profile_fields(user_profile)
        self._save_address_data(user_profile)
        user_profile.save()
        return user_profile

    def _save_profile_fields(self, user_profile):
        """Update UserProfile fields"""
        user_profile.roster_id = self.cleaned_data.get("roster_id")
        user_profile.drivers_license_id = self.cleaned_data.get("drivers_license_id")

    def _save_address_data(self, user_profile):
        """Handle address data creation/update"""
        address_data = {
            "street_1": self.cleaned_data.get("street_1"),
            "street_2": self.cleaned_data.get("street_2"),
            "city": self.cleaned_data.get("city"),
            "state": self.cleaned_data.get("state"),
            "zip_code": self.cleaned_data.get("zip_code"),
        }

        # Check if we have required address fields
        if self._has_required_address_fields(address_data):
            self._create_or_update_address(user_profile, address_data)
        elif not any(address_data.values()):
            # If all address fields are empty, remove the address reference
            user_profile.address = None

    def _has_required_address_fields(self, address_data):
        """Check if required address fields are provided"""
        return (
            address_data["street_1"]
            and address_data["city"]
            and address_data["state"]
            and address_data["zip_code"]
        )

    def _create_or_update_address(self, user_profile, address_data):
        """Create or update address with coordinate handling"""
        latitude = self.cleaned_data.get("latitude")
        longitude = self.cleaned_data.get("longitude")

        if user_profile.address:
            self._update_existing_address(user_profile.address, address_data, latitude, longitude)
        else:
            self._create_new_address(user_profile, address_data, latitude, longitude)

    def _update_existing_address(self, address, address_data, latitude, longitude):
        """Update existing address"""
        for field, value in address_data.items():
            setattr(address, field, value)
        self._set_coordinates(address, latitude, longitude)
        address.save()

    def _create_new_address(self, user_profile, address_data, latitude, longitude):
        """Create new address"""
        address = Address.objects.create(**address_data)
        self._set_coordinates(address, latitude, longitude)
        if latitude is not None and longitude is not None:
            address.save()
        user_profile.address = address

    def _set_coordinates(self, address, latitude, longitude):
        """Set coordinates on address if provided"""
        if latitude is not None and longitude is not None:
            address.set_coordinates(longitude, latitude)
            address.location_accuracy = "EXACT"
        elif not address.location:
            address.location = None
            address.location_accuracy = None


class PublicUserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "public_bio",
            "public_bio_visible",
            "public_phone",
            "public_phone_visible",
            "public_email",
            "public_email_visible",
            "public_visible",
            "use_gravatar",
            "gravatar_email",
        ]
        widgets = {
            "public_bio": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Short public bio"}
            ),
            "public_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Public phone number"}
            ),
            "public_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Public email address"}
            ),
            "public_bio_visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "public_phone_visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "public_email_visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "public_visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "use_gravatar": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "gravatar_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email for Gravatar (optional)"}
            ),
        }


class ContactForm(ModelForm):
    """
    Form for creating/editing user contact information
    """

    class Meta:
        model = Contact
        fields = ["contact_type", "value", "organization", "is_primary"]
        widgets = {
            "contact_type": forms.Select(
                attrs={"class": "form-select"}, choices=Contact.CONTACT_TYPES
            ),
            "value": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter email or phone number"}
            ),
            "organization": forms.Select(attrs={"class": "form-select"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter organization choices to user's memberships
        if self.user:
            from operations.models import IncidentOrganization
            from organizations.models import OrganizationUser

            user_orgs = OrganizationUser.objects.filter(user=self.user).values_list(
                "organization_id", flat=True
            )
            self.fields["organization"].queryset = IncidentOrganization.objects.filter(
                id__in=user_orgs
            )

        # Add empty choice for organization (global contact)
        org_choices = list(self.fields["organization"].choices)
        org_choices.insert(0, ("", "Global (no organization)"))
        self.fields["organization"].choices = org_choices
        self.fields["organization"].required = False

    def clean_value(self):
        """Validate contact value based on contact type"""
        value = self.cleaned_data.get("value", "").strip()
        contact_type = self.cleaned_data.get("contact_type")

        if not value:
            raise forms.ValidationError("Contact value is required.")

        if contact_type == "EMAIL":
            from django.core.validators import EmailValidator

            validator = EmailValidator()
            try:
                validator(value)
            except forms.ValidationError:
                raise forms.ValidationError("Enter a valid email address.")

        elif contact_type == "PHONE":
            # Basic phone validation - allow digits, spaces, hyphens, parentheses, plus
            if not re.match(r"^[\d\-\(\)\s\+\.]+$", value):
                raise forms.ValidationError(
                    "Enter a valid phone number (digits, spaces, hyphens, parentheses, and plus signs only)."
                )

        return value

    def clean(self):
        """Additional validation for contact constraints"""
        cleaned_data = super().clean()

        if not self.user:
            raise forms.ValidationError("User must be specified.")

        contact_type = cleaned_data.get("contact_type")
        value = cleaned_data.get("value")
        organization = cleaned_data.get("organization")

        # Check for duplicate contact
        if contact_type and value:
            existing = Contact.objects.filter(
                user=self.user,
                contact_type=contact_type,
                value=value,
                organization=organization,
                is_active=True,
            )

            # Exclude current instance if editing
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    f"A {contact_type.lower()} contact with this value already exists for this organization context."
                )

        return cleaned_data

    def save(self, commit=True):
        """Save the contact with proper primary contact handling"""
        contact = super().save(commit=False)
        contact.user = self.user

        if commit:
            # If setting as primary, unset other primary contacts of same type
            if contact.is_primary:
                Contact.objects.filter(
                    user=self.user,
                    organization=contact.organization,
                    contact_type=contact.contact_type,
                    is_primary=True,
                    is_active=True,
                ).update(is_primary=False)

            contact.save()

        return contact


class ContactDeleteForm(forms.Form):
    """
    Form for confirming contact deletion (soft delete)
    """

    confirm = forms.BooleanField(
        required=True,
        label="I confirm I want to delete this contact",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
