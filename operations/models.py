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
