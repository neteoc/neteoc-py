from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from organizations.abstract import (
    AbstractOrganization,
    AbstractOrganizationUser,
    AbstractOrganizationOwner,
    AbstractOrganizationInvitation,
)

# Create your models here.


class IncidentOrganization(AbstractOrganization):
    """
    Custom organization model for incident management.
    Represents an organization (agency, department, volunteer group) that responds to incidents.
    """

    ORGANIZATION_TYPES = [
        ("FIRE", "Fire Department"),
        ("POLICE", "Police Department"),
        ("EMS", "Emergency Medical Services"),
        ("EMERGENCY_MGMT", "Emergency Management"),
        ("PUBLIC_WORKS", "Public Works"),
        ("VOLUNTEER", "Volunteer Organization"),
        ("NGO", "Non-Governmental Organization"),
        ("PRIVATE", "Private Company"),
        ("FEDERAL", "Federal Agency"),
        ("STATE", "State Agency"),
        ("LOCAL", "Local Government"),
        ("OTHER", "Other"),
    ]

    organization_type = models.CharField(
        max_length=20, choices=ORGANIZATION_TYPES, default="OTHER", help_text="Type of organization"
    )
    contact_email = models.EmailField(
        blank=True, help_text="Primary contact email for the organization"
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, help_text="Primary contact phone number"
    )
    address = models.TextField(blank=True, help_text="Physical address of the organization")
    website = models.URLField(blank=True, help_text="Organization website URL")
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this organization has been verified by system administrators",
    )

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return f"{self.name} ({self.get_organization_type_display()})"


class IncidentOrganizationUser(AbstractOrganizationUser):
    """
    Links users to organizations with specific roles and permissions.
    """

    ROLE_CHOICES = [
        ("ADMIN", "Administrator"),
        ("INCIDENT_MANAGER", "Incident Manager"),
        ("RESPONDER", "Responder"),
        ("VIEWER", "Viewer"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="VIEWER",
        help_text="User's role within the organization",
    )
    can_create_incidents = models.BooleanField(
        default=False, help_text="Whether this user can create new incidents for the organization"
    )
    can_manage_users = models.BooleanField(
        default=False,
        help_text="Whether this user can invite/manage other users in the organization",
    )

    class Meta:
        verbose_name = "Organization User"
        verbose_name_plural = "Organization Users"
        unique_together = ["organization", "user"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.organization.name} ({self.get_role_display()})"


class IncidentOrganizationOwner(AbstractOrganizationOwner):
    """
    Identifies the owner of an organization (there can be only one).
    """

    class Meta:
        verbose_name = "Organization Owner"
        verbose_name_plural = "Organization Owners"


class IncidentOrganizationInvitation(AbstractOrganizationInvitation):
    """
    Stores invitations for users to join organizations.
    """

    role = models.CharField(
        max_length=20,
        choices=IncidentOrganizationUser.ROLE_CHOICES,
        default="VIEWER",
        help_text="Role the user will have when they accept the invitation",
    )
    can_create_incidents = models.BooleanField(
        default=False, help_text="Whether the invited user will be able to create incidents"
    )
    can_manage_users = models.BooleanField(
        default=False, help_text="Whether the invited user will be able to manage other users"
    )

    class Meta:
        verbose_name = "Organization Invitation"
        verbose_name_plural = "Organization Invitations"


class Incident(models.Model):
    """
    Represents a disaster or community event (hurricane, flood, festival, etc.)
    People check in/out of specific incidents
    """

    INCIDENT_TYPES = [
        ("HURRICANE", "Hurricane"),
        ("FLOOD", "Flood"),
        ("WILDFIRE", "Wildfire"),
        ("EARTHQUAKE", "Earthquake"),
        ("TORNADO", "Tornado"),
        ("WINTER_STORM", "Winter Storm"),
        ("FESTIVAL", "Community Festival"),
        ("TRAINING", "Training Exercise"),
        ("OTHER", "Other"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("CLOSED", "Closed"),
        ("STANDBY", "Standby"),
    ]

    name = models.CharField(
        max_length=200,
        help_text="Name of the incident (e.g., 'Hurricane Milton Response', 'County Fair 2025')",
    )
    incident_type = models.CharField(
        max_length=20, choices=INCIDENT_TYPES, help_text="Type of incident or event"
    )
    description = models.TextField(
        blank=True, default="", help_text="Additional details about the incident"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        help_text="Current status of the incident",
    )
    start_date = models.DateTimeField(
        default=timezone.now, help_text="When the incident began or is scheduled to begin"
    )
    end_date = models.DateTimeField(
        blank=True, null=True, help_text="When the incident ended (leave blank if ongoing)"
    )
    location = models.CharField(
        max_length=200, blank=True, default="", help_text="Primary location of the incident"
    )
    organization = models.ForeignKey(
        "IncidentOrganization",
        on_delete=models.CASCADE,
        related_name="incidents",
        help_text="The organization that owns this incident",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_incidents",
        help_text="The user who owns and has full control over this incident",
    )
    incident_commander = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commanded_incidents",
        help_text="The incident commander - primary point of contact for this incident",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_incidents",
        help_text="Admin user who created this incident",
    )
    # Incident linking fields for multi-organization coordination
    parent_incident = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_incidents",
        help_text="Parent incident that this incident supports or is related to",
    )
    support_request = models.ForeignKey(
        "SupportRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_incidents",
        help_text="Support request that led to the creation of this incident",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"

    def __str__(self):
        return f"{self.name} ({self.get_incident_type_display()})"

    @property
    def is_active(self):
        """Check if the incident is currently active"""
        return self.status == "ACTIVE"

    @property
    def total_checkins(self):
        """Get total number of check-ins for this incident"""
        return self.checkins.count()

    @property
    def active_checkins(self):
        """Get number of people currently checked in (not checked out)"""
        return self.checkins.filter(Check_Out=False).count()

    def has_admin_access(self, user):
        """Check if user has admin access to this incident"""
        if not user.is_authenticated:
            return False

        # System superuser/staff always have access
        if user.is_superuser or user.is_staff:
            return True

        # Owner has full admin access
        if self.owner == user:
            return True

        # Check organization membership and permissions
        try:
            org_user = IncidentOrganizationUser.objects.get(
                organization=self.organization, user=user
            )
            # Admins and incident managers can admin incidents
            if org_user.role in ["ADMIN", "INCIDENT_MANAGER"]:
                return True
        except IncidentOrganizationUser.DoesNotExist:
            pass

        # Legacy group-based permissions (for backwards compatibility)
        if user.groups.filter(name="Incident Admins").exists():
            return True

        return False

    def has_read_access(self, user):
        """Check if user has read access to this incident"""
        if not user.is_authenticated:
            return False

        # Admin access includes read access
        if self.has_admin_access(user):
            return True

        # Check organization membership
        try:
            IncidentOrganizationUser.objects.get(organization=self.organization, user=user)
            # All organization members can read incidents
            return True
        except IncidentOrganizationUser.DoesNotExist:
            pass

        # Legacy group-based permissions (for backwards compatibility)
        if user.groups.filter(name="Incident Viewers").exists():
            return True

        return False

    def has_write_access(self, user):
        """Check if user has write access (can create/edit check-ins) to this incident"""
        if not user.is_authenticated:
            return False

        # Admin access includes write access
        if self.has_admin_access(user):
            return True

        # Check organization membership and permissions
        try:
            org_user = IncidentOrganizationUser.objects.get(
                organization=self.organization, user=user
            )
            # Responders can write to incidents
            if org_user.role in ["RESPONDER", "INCIDENT_MANAGER"]:
                return True
        except IncidentOrganizationUser.DoesNotExist:
            pass

        # Legacy group-based permissions (for backwards compatibility)
        if user.groups.filter(name="Incident Responders").exists():
            return True

        return False

    def can_user_create_incidents_for_org(self, user):
        """Check if user can create incidents for this incident's organization"""
        if not user.is_authenticated:
            return False

        # System superuser/staff can create incidents
        if user.is_superuser or user.is_staff:
            return True

        # Check organization membership and permissions
        try:
            org_user = IncidentOrganizationUser.objects.get(
                organization=self.organization, user=user
            )
            return org_user.can_create_incidents
        except IncidentOrganizationUser.DoesNotExist:
            return False


class CheckIn(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="checkins",
        help_text="The incident this check-in is associated with",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The Django user this check-in is for (optional - person may not have a user account)",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    roster_id = models.CharField(max_length=7, help_text="Example: DOE1234")
    mileage = models.IntegerField(
        help_text="Round trip miles driven today.Rounded to nearest mile i.e. 123"
    )
    food_expenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Dollar amount spent on food today. i.e. 12.34",
    )
    other_expenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Dollar amount spent on other expenses today. i.e. 64.88",
    )
    expense_notes = models.TextField(
        blank=True,
        default="",
        help_text="Explain any large expenses or unusual mileage.",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    Check_Out = models.BooleanField(
        default=False, help_text="Check this box if you are checking out for the day."
    )
    checkout_time = models.DateTimeField(
        blank=True, null=True, help_text="The time you checked out for the day."
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Check-in"
        verbose_name_plural = "Check-ins"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.incident.name}"


class SupportRequest(models.Model):
    """
    Represents a request for support from one organization to another
    Example: EMA requesting support from State Defense Force for hurricane response
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("DECLINED", "Declined"),
        ("FULFILLED", "Fulfilled"),
        ("CANCELLED", "Cancelled"),
    ]

    URGENCY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    # Request details
    title = models.CharField(max_length=200, help_text="Brief title of the support request")
    description = models.TextField(help_text="Detailed description of what support is needed")
    urgency = models.CharField(
        max_length=10,
        choices=URGENCY_CHOICES,
        default="MEDIUM",
        help_text="Urgency level of the request",
    )

    # Organizations involved
    requesting_organization = models.ForeignKey(
        "IncidentOrganization",
        on_delete=models.CASCADE,
        related_name="outgoing_support_requests",
        help_text="Organization requesting support",
    )
    target_organization = models.ForeignKey(
        "IncidentOrganization",
        on_delete=models.CASCADE,
        related_name="incoming_support_requests",
        help_text="Organization being asked to provide support",
    )

    # Related incident
    related_incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="support_requests",
        help_text="The incident that needs support",
    )

    # Request management
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_support_requests",
        help_text="User who created this support request",
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_support_requests",
        help_text="User who reviewed this request",
    )

    # Status and timing
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        help_text="Current status of the support request",
    )
    requested_start_date = models.DateTimeField(help_text="When support is needed to start")
    requested_end_date = models.DateTimeField(
        null=True, blank=True, help_text="When support is expected to end (optional)"
    )

    # Response details
    response_notes = models.TextField(blank=True, help_text="Notes from the reviewing organization")
    approved_resources = models.TextField(
        blank=True, help_text="Description of what resources were approved"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(
        null=True, blank=True, help_text="When the request was reviewed"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Support Request"
        verbose_name_plural = "Support Requests"

    def __str__(self):
        return (
            f"{self.title} - {self.requesting_organization.name} → {self.target_organization.name}"
        )

    @property
    def is_pending(self):
        return self.status == "PENDING"

    @property
    def is_approved(self):
        return self.status == "APPROVED"

    @property
    def can_create_incident(self):
        """Check if this approved request can be used to create a supporting incident"""
        return self.status == "APPROVED" and not hasattr(self, "created_incidents")


class IncidentLink(models.Model):
    """
    Represents a relationship between two incidents, typically from different organizations
    This allows tracking of coordinated response efforts
    """

    RELATIONSHIP_TYPES = [
        ("SUPPORTS", "Supports - this incident supports the linked incident"),
        ("SUPPORTED_BY", "Supported By - this incident is supported by the linked incident"),
        ("COORDINATES", "Coordinates - incidents are coordinating together"),
        ("RELATED", "Related - incidents are related but not directly supporting"),
    ]

    from_incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="outgoing_links",
        help_text="The incident this link originates from",
    )
    to_incident = models.ForeignKey(
        "Incident",
        on_delete=models.CASCADE,
        related_name="incoming_links",
        help_text="The incident this link points to",
    )
    relationship_type = models.CharField(
        max_length=15,
        choices=RELATIONSHIP_TYPES,
        help_text="Type of relationship between incidents",
    )
    notes = models.TextField(blank=True, help_text="Additional notes about the relationship")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="User who created this link"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["from_incident", "to_incident", "relationship_type"]]
        verbose_name = "Incident Link"
        verbose_name_plural = "Incident Links"

    def __str__(self):
        return f"{self.from_incident.name} {self.get_relationship_type_display()} {self.to_incident.name}"


# Asset Management Models


class AssetCategory(models.Model):
    """
    Categories for assets that define special data requirements
    Examples: Vehicles, Radios, Laptops, Medical Equipment
    """

    name = models.CharField(max_length=100, help_text="Name of the asset category")
    description = models.TextField(blank=True, help_text="Description of this asset category")
    requires_license = models.BooleanField(
        default=False, help_text="Whether assets in this category require a license to operate"
    )
    requires_training = models.BooleanField(
        default=False, help_text="Whether assets in this category require special training"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asset Category"
        verbose_name_plural = "Asset Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Asset(models.Model):
    """
    Represents a trackable asset belonging to an organization
    Examples: Radios, laptops, vehicles, medical equipment
    """

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("IN_USE", "In Use"),
        ("MAINTENANCE", "Under Maintenance"),
        ("RETIRED", "Retired"),
        ("LOST", "Lost"),
        ("DAMAGED", "Damaged"),
    ]

    # Basic asset information
    identifier = models.CharField(
        max_length=50,
        help_text="Unique identifier for the asset (asset tag, serial number, etc.)",
    )
    name = models.CharField(max_length=200, help_text="Name or model of the asset")
    description = models.TextField(blank=True, help_text="Detailed description of the asset")
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.CASCADE,
        related_name="assets",
        help_text="Category this asset belongs to",
    )

    # Ownership and location
    organization = models.ForeignKey(
        IncidentOrganization,
        on_delete=models.CASCADE,
        related_name="assets",
        help_text="Organization that owns this asset",
    )
    current_holder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="held_assets",
        help_text="User currently holding this asset",
    )
    current_incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets_in_use",
        help_text="Incident this asset is currently being used for",
    )

    # Status and tracking
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="AVAILABLE",
        help_text="Current status of the asset",
    )
    location = models.CharField(
        max_length=200, blank=True, help_text="Current location of the asset"
    )

    # Asset-specific fields (extensible for special categories)
    serial_number = models.CharField(
        max_length=100, blank=True, help_text="Serial number of the asset"
    )
    purchase_date = models.DateField(
        null=True, blank=True, help_text="Date the asset was purchased"
    )
    warranty_expiration = models.DateField(
        null=True, blank=True, help_text="Date the warranty expires"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Purchase or estimated value of the asset",
    )

    # Radio-specific fields (when category is radio)
    frequency = models.CharField(
        max_length=50, blank=True, help_text="Radio frequency (for radio assets)"
    )
    call_sign = models.CharField(
        max_length=20, blank=True, help_text="Call sign (for radio assets)"
    )

    # Vehicle-specific fields (when category is vehicle)
    license_plate = models.CharField(
        max_length=20, blank=True, help_text="License plate number (for vehicle assets)"
    )
    vin = models.CharField(
        max_length=17, blank=True, help_text="Vehicle Identification Number (for vehicle assets)"
    )
    fuel_type = models.CharField(
        max_length=20, blank=True, help_text="Type of fuel used (for vehicle assets)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["organization", "identifier"]]
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ["identifier", "name"]

    def __str__(self):
        return f"{self.identifier} - {self.name}"

    @property
    def is_available(self):
        """Check if the asset is available for checkout"""
        return self.status == "AVAILABLE"

    @property
    def is_in_use(self):
        """Check if the asset is currently in use"""
        return self.status == "IN_USE"

    def can_user_checkout(self, user):
        """Check if a user can checkout this asset"""
        if not user.is_authenticated:
            return False

        # Asset must be available
        if not self.is_available:
            return False

        # User must be a member of the asset's organization
        try:
            IncidentOrganizationUser.objects.get(organization=self.organization, user=user)
            return True
        except IncidentOrganizationUser.DoesNotExist:
            return False

    def can_user_manage(self, user):
        """Check if a user can manage (edit/delete) this asset"""
        if not user.is_authenticated:
            return False

        # Superusers can manage all assets
        if user.is_superuser:
            return True

        # Check organization membership and role
        try:
            org_user = IncidentOrganizationUser.objects.get(
                organization=self.organization, user=user
            )
            # Admins can manage assets
            if org_user.role == "ADMIN":
                return True
        except IncidentOrganizationUser.DoesNotExist:
            pass

        return False


class AssetCheckout(models.Model):
    """
    Represents a checkout/checkin transaction for an asset
    Implements a two-step process: checkout (pending) -> checkin (completed)
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending - Waiting for new holder to accept"),
        ("ACTIVE", "Active - Asset is checked out"),
        ("COMPLETED", "Completed - Asset has been checked back in"),
        ("CANCELLED", "Cancelled - Checkout was cancelled"),
    ]

    # Asset and users involved
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="checkouts",
        help_text="Asset being checked out",
    )
    checked_out_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="asset_checkouts_given",
        help_text="User who initiated the checkout (current holder)",
    )
    checked_out_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="asset_checkouts_received",
        help_text="User receiving the asset",
    )

    # Incident and purpose
    incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="asset_checkouts",
        help_text="Incident the asset is being checked out for",
    )
    purpose = models.TextField(blank=True, help_text="Purpose or reason for checking out the asset")

    # Status and timing
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
        help_text="Current status of the checkout",
    )
    checkout_time = models.DateTimeField(
        auto_now_add=True, help_text="When the checkout was initiated"
    )
    accepted_time = models.DateTimeField(
        null=True, blank=True, help_text="When the new holder accepted the asset"
    )
    checkin_time = models.DateTimeField(
        null=True, blank=True, help_text="When the asset was checked back in"
    )

    # Condition tracking
    checkout_condition = models.TextField(
        blank=True, help_text="Condition of the asset at checkout"
    )
    checkin_condition = models.TextField(blank=True, help_text="Condition of the asset at checkin")
    issues_reported = models.TextField(
        blank=True, help_text="Any issues or damage reported during checkout"
    )

    # Location tracking
    checkout_location = models.CharField(
        max_length=200, blank=True, help_text="Location where checkout occurred"
    )
    checkin_location = models.CharField(
        max_length=200, blank=True, help_text="Location where checkin occurred"
    )

    class Meta:
        verbose_name = "Asset Checkout"
        verbose_name_plural = "Asset Checkouts"
        ordering = ["-checkout_time"]

    def __str__(self):
        return f"{self.asset.identifier} - {self.checked_out_by.get_full_name() or self.checked_out_by.username} → {self.checked_out_to.get_full_name() or self.checked_out_to.username}"

    @property
    def is_pending(self):
        """Check if the checkout is pending acceptance"""
        return self.status == "PENDING"

    @property
    def is_active(self):
        """Check if the checkout is active (asset is checked out)"""
        return self.status == "ACTIVE"

    @property
    def is_completed(self):
        """Check if the checkout is completed (asset checked back in)"""
        return self.status == "COMPLETED"

    def can_user_accept(self, user):
        """Check if a user can accept this pending checkout"""
        return self.is_pending and self.checked_out_to == user

    def can_user_checkin(self, user):
        """Check if a user can check in this asset"""
        return self.is_active and self.checked_out_to == user

    def can_user_cancel(self, user):
        """Check if a user can cancel this checkout"""
        if not self.is_pending:
            return False

        # Either person involved can cancel, or asset managers
        if user in [self.checked_out_by, self.checked_out_to]:
            return True

        # Asset managers can cancel
        return self.asset.can_user_manage(user)

    def accept_checkout(self, user, condition_notes="", location=""):
        """Accept a pending checkout"""
        if not self.can_user_accept(user):
            raise ValueError("User cannot accept this checkout")

        self.status = "ACTIVE"
        self.accepted_time = timezone.now()
        if condition_notes:
            self.checkout_condition = condition_notes
        if location:
            self.checkout_location = location
        self.save()

        # Update asset status and holder
        self.asset.status = "IN_USE"
        self.asset.current_holder = self.checked_out_to
        if self.incident:
            self.asset.current_incident = self.incident
        self.asset.save()

    def checkin_asset(self, user, condition_notes="", location="", issues=""):
        """Check in an active asset"""
        if not self.can_user_checkin(user):
            raise ValueError("User cannot check in this asset")

        self.status = "COMPLETED"
        self.checkin_time = timezone.now()
        if condition_notes:
            self.checkin_condition = condition_notes
        if location:
            self.checkin_location = location
        if issues:
            self.issues_reported = issues
        self.save()

        # Update asset status and clear holder
        self.asset.status = "AVAILABLE"
        self.asset.current_holder = None
        self.asset.current_incident = None
        self.asset.save()

    def cancel_checkout(self, user):
        """Cancel a pending checkout"""
        if not self.can_user_cancel(user):
            raise ValueError("User cannot cancel this checkout")

        self.status = "CANCELLED"
        self.save()
