from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


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
