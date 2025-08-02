from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import (
    CheckIn,
    Incident,
    IncidentOrganization,
    IncidentOrganizationUser,
    SupportRequest,
    AssetCategory,
    Asset,
    AssetCheckout,
    TimeEntry,
)
from logging import getLogger
import re

logger = getLogger(__name__)


class IncidentForm(ModelForm):
    """Form for creating and editing incidents"""

    organization = forms.ModelChoiceField(
        queryset=IncidentOrganization.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select organization --",
        help_text="The organization responsible for this incident",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    incident_commander = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="-- Select incident commander --",
        help_text="The incident commander serves as the primary point of contact",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        help_text="When the incident began or is scheduled to begin",
    )

    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        help_text="When the incident ended (leave blank if ongoing)",
    )

    class Meta:
        model = Incident
        fields = [
            "name",
            "organization",
            "incident_type",
            "description",
            "status",
            "start_date",
            "end_date",
            "location",
            "incident_commander",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "incident_type": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set user-friendly display names for incident commanders
        self.fields["incident_commander"].label_from_instance = self.user_label_from_instance

        # Set default start_date to now if not provided
        if not self.instance.pk and not self.initial.get("start_date"):
            from django.utils import timezone

            self.initial["start_date"] = timezone.now().strftime("%Y-%m-%dT%H:%M")

    def user_label_from_instance(self, user):
        """Show user's full name and username for better identification"""
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name} ({user.username})"
        return user.username


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
        # Extract incident from kwargs if provided
        self.incident = kwargs.pop("incident", None)
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


class OrganizationForm(ModelForm):
    """Form for creating and editing organizations"""

    class Meta:
        model = IncidentOrganization
        fields = ["name", "organization_type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "organization_type": forms.Select(attrs={"class": "form-control"}),
        }


class InviteUserForm(forms.Form):
    """Form for inviting users to an organization"""

    invitee_identifier = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        help_text="Email address of the person to invite",
        label="Email",
    )

    role = forms.ChoiceField(
        choices=IncidentOrganizationUser.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Role to assign to the invited user",
    )


class ManageUserRoleForm(ModelForm):
    """Form for managing user roles within an organization"""

    class Meta:
        model = IncidentOrganizationUser
        fields = ["role", "is_admin"]
        widgets = {
            "role": forms.Select(attrs={"class": "form-control"}),
            "is_admin": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SupportRequestForm(ModelForm):
    """Form for creating support requests between organizations"""

    target_organization = forms.ModelChoiceField(
        queryset=IncidentOrganization.objects.all(),
        required=True,
        empty_label="-- Select organization to request support from --",
        help_text="The organization you want to request support from (cannot be the same as requesting organization)",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    related_incident = forms.ModelChoiceField(
        queryset=Incident.objects.none(),  # Will be populated in __init__
        required=True,
        empty_label="-- Select incident that needs support --",
        help_text="The incident that requires support",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    requested_start_date = forms.DateField(
        required=True,
        help_text="When the support is needed to start",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    requested_end_date = forms.DateField(
        required=True,
        help_text="When the support is needed to end",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    class Meta:
        model = SupportRequest
        fields = [
            "title",
            "description",
            "urgency",
            "target_organization",
            "related_incident",
            "requested_start_date",
            "requested_end_date",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "urgency": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        requesting_organization = kwargs.pop("requesting_organization", None)
        current_incident = kwargs.pop("current_incident", None)
        super().__init__(*args, **kwargs)

        if user:
            # Populate incidents from user's organizations
            user_orgs = IncidentOrganizationUser.objects.filter(user=user).values_list(
                "organization", flat=True
            )
            self.fields["related_incident"].queryset = Incident.objects.filter(
                organization__in=user_orgs, status="ACTIVE"
            )

            # Set the current incident as the default if provided
            if current_incident and current_incident.id in self.fields[
                "related_incident"
            ].queryset.values_list("id", flat=True):
                self.fields["related_incident"].initial = current_incident.id

            # Exclude the requesting organization from target options
            # An organization cannot request support from itself
            target_queryset = IncidentOrganization.objects.all()
            if requesting_organization:
                target_queryset = target_queryset.exclude(id=requesting_organization.id)

            self.fields["target_organization"].queryset = target_queryset


# Asset Management Forms


class AssetCategoryForm(ModelForm):
    """Form for creating and editing asset categories"""

    class Meta:
        model = AssetCategory
        fields = ["name", "description", "requires_license", "requires_training"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "requires_license": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "requires_training": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AssetForm(ModelForm):
    """Form for creating and editing assets"""

    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.all(),
        required=True,
        empty_label="-- Select category --",
        help_text="Category this asset belongs to",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    organization = forms.ModelChoiceField(
        queryset=IncidentOrganization.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select organization --",
        help_text="Organization that owns this asset",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    purchase_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        help_text="Date the asset was purchased",
    )

    warranty_expiration = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        help_text="Date the warranty expires",
    )

    class Meta:
        model = Asset
        fields = [
            "identifier",
            "name",
            "description",
            "category",
            "organization",
            "status",
            "location",
            "serial_number",
            "purchase_date",
            "warranty_expiration",
            "value",
            "frequency",
            "call_sign",
            "license_plate",
            "vin",
            "fuel_type",
        ]
        widgets = {
            "identifier": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "frequency": forms.TextInput(attrs={"class": "form-control"}),
            "call_sign": forms.TextInput(attrs={"class": "form-control"}),
            "license_plate": forms.TextInput(attrs={"class": "form-control"}),
            "vin": forms.TextInput(attrs={"class": "form-control"}),
            "fuel_type": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            # Filter organizations to only those the user belongs to
            user_orgs = IncidentOrganizationUser.objects.filter(user=user).values_list(
                "organization", flat=True
            )
            self.fields["organization"].queryset = IncidentOrganization.objects.filter(
                id__in=user_orgs, is_active=True
            )

    def clean_identifier(self):
        """Validate that identifier is unique within the organization"""
        identifier = self.cleaned_data.get("identifier")
        organization = self.cleaned_data.get("organization")

        if identifier and organization:
            # Check for existing asset with same identifier in same organization
            existing = Asset.objects.filter(
                identifier=identifier, organization=organization
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing.exists():
                raise forms.ValidationError(
                    f"An asset with identifier '{identifier}' already exists in {organization.name}"
                )

        return identifier


class AssetCheckoutForm(ModelForm):
    """Form for checking out an asset to another user"""

    checked_out_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select user to check out to --",
        help_text="User who will receive the asset",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    incident = forms.ModelChoiceField(
        queryset=Incident.objects.none(),  # Will be populated in __init__
        required=False,
        empty_label="-- Select incident (optional) --",
        help_text="Incident the asset is being checked out for",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = AssetCheckout
        fields = [
            "checked_out_to",
            "incident",
            "purpose",
            "checkout_condition",
            "checkout_location",
        ]
        widgets = {
            "purpose": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "checkout_condition": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "checkout_location": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        asset = kwargs.pop("asset", None)
        super().__init__(*args, **kwargs)

        if user and asset:
            # Populate users from the asset's organization
            asset_org_users = IncidentOrganizationUser.objects.filter(
                organization=asset.organization
            ).values_list("user", flat=True)
            self.fields["checked_out_to"].queryset = User.objects.filter(
                id__in=asset_org_users, is_active=True
            ).order_by("first_name", "last_name", "username")

            # Populate active incidents from the asset's organization
            self.fields["incident"].queryset = Incident.objects.filter(
                organization=asset.organization, status="ACTIVE"
            ).order_by("-start_date")

            # Custom display for users showing full name if available
            self.fields["checked_out_to"].label_from_instance = self.user_label_from_instance

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


class AssetAcceptForm(forms.Form):
    """Form for accepting a pending asset checkout"""

    condition_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        help_text="Note the condition of the asset when you receive it",
        label="Asset Condition",
    )

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Location where you received the asset",
        label="Pickup Location",
    )


class AssetCheckinForm(forms.Form):
    """Form for checking in an asset"""

    condition_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        help_text="Note the condition of the asset when returning it",
        label="Asset Condition",
    )

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Location where you are returning the asset",
        label="Return Location",
    )

    issues_reported = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        help_text="Report any issues, damage, or problems with the asset",
        label="Issues or Damage",
    )


class TimeEntryForm(ModelForm):
    """Form for creating and editing time entries"""
    
    class Meta:
        model = TimeEntry
        fields = [
            'organization',
            'incident', 
            'date',
            'activity_description',
            'work_hours',
            'volunteer_hours', 
            'travel_hours',
            'travel_miles',
            'travel_meal_costs',
            'billeting_costs',
            'purchases',
            'purchase_explanation',
        ]
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'incident': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activity_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'work_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'volunteer_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'travel_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'travel_miles': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'travel_meal_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'billeting_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'purchases': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'purchase_explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Required when purchases > $0. Explain what was purchased and why it was necessary...'}),
        }
        labels = {
            'organization': 'Organization',
            'incident': 'Incident (Optional)',
            'date': 'Date',
            'activity_description': 'Activity Description',
            'work_hours': 'Work Hours',
            'volunteer_hours': 'Volunteer Hours',
            'travel_hours': 'Travel Hours',
            'travel_miles': 'Travel Miles',
            'travel_meal_costs': 'Travel Meal Costs ($)',
            'billeting_costs': 'Billeting/Lodging Costs ($)',
            'purchases': 'Purchases ($)',
            'purchase_explanation': 'Purchase Notes & Explanation',
        }
        help_texts = {
            'activity_description': 'Describe the work performed during this time period',
            'work_hours': 'Paid hours worked (use 0.25 for 15-minute increments)',
            'volunteer_hours': 'Unpaid volunteer hours (use 0.25 for 15-minute increments)',
            'travel_hours': 'Hours spent traveling to/from work location',
            'travel_miles': 'Round trip miles driven for organization work',
            'travel_meal_costs': 'Cost of meals while traveling for work',
            'billeting_costs': 'Cost of lodging or accommodation',
            'purchases': 'Cost of equipment, supplies, or other items purchased',
            'purchase_explanation': 'Required when purchases > $0. Explain what was purchased and the business reason.',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter organizations to those the user belongs to
            self.fields['organization'].queryset = IncidentOrganization.objects.filter(
                users=user, is_active=True
            )
            
            # Filter incidents to those the user has access to
            user_orgs = IncidentOrganization.objects.filter(users=user)
            self.fields['incident'].queryset = Incident.objects.filter(
                organization__in=user_orgs
            ).select_related('organization')
            
        # Set empty labels
        self.fields['organization'].empty_label = "-- Select Organization --"
        self.fields['incident'].empty_label = "-- Select Incident (Optional) --"
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that at least one hour type is greater than 0
        work_hours = cleaned_data.get('work_hours', 0)
        volunteer_hours = cleaned_data.get('volunteer_hours', 0)
        travel_hours = cleaned_data.get('travel_hours', 0)
        
        if work_hours == 0 and volunteer_hours == 0 and travel_hours == 0:
            raise forms.ValidationError("At least one type of hours must be greater than 0.")
        
        # If purchases > 0, explanation is required
        purchases = cleaned_data.get('purchases', 0)
        purchase_explanation = cleaned_data.get('purchase_explanation', '').strip()
        
        if purchases and purchases > 0 and not purchase_explanation:
            self.add_error('purchase_explanation', 
                "Purchase notes are required when a purchase amount is entered. Please explain what was purchased and why it was necessary.")
        
        return cleaned_data
