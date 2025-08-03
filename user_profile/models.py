from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import math

# Create your models here.


class Address(models.Model):
    """
    Normalized address model with coordinate support for disaster response
    Ready for GeoDjango migration when spatial database backend is configured
    """

    street_1 = models.CharField(max_length=100, help_text="Street address line 1")
    street_2 = models.CharField(
        max_length=100, blank=True, default="", help_text="Street address line 2 (optional)"
    )
    city = models.CharField(max_length=50, help_text="City name")
    state = models.CharField(max_length=2, help_text="State abbreviation (e.g., CA, NY)")
    zip_code = models.CharField(max_length=10, help_text="ZIP code")

    # Coordinate fields (compatible with GeoDjango Point field when migrated)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        help_text="Latitude coordinate (WGS84)",
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        help_text="Longitude coordinate (WGS84)",
    )

    # Additional spatial metadata
    location_accuracy = models.CharField(
        max_length=20,
        blank=True,
        default="",
        choices=[
            ("EXACT", "Exact"),
            ("APPROXIMATE", "Approximate"),
            ("CITY", "City Level"),
            ("ZIP", "ZIP Code Level"),
            ("UNKNOWN", "Unknown"),
        ],
        help_text="Accuracy level of the geographic location",
    )

    # Geocoding metadata
    geocoded_at = models.DateTimeField(
        blank=True, null=True, help_text="When the address was geocoded"
    )
    geocoding_source = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Source used for geocoding (e.g., Google, OpenStreetMap)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        indexes = [
            models.Index(fields=["state", "city"]),
            models.Index(fields=["zip_code"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        address_parts = [self.street_1]
        if self.street_2:
            address_parts.append(self.street_2)
        return f"{', '.join(address_parts)}, {self.city}, {self.state} {self.zip_code}"

    def set_coordinates(self, longitude, latitude):
        """Set coordinates using longitude and latitude"""
        if longitude is not None and latitude is not None:
            self.longitude = longitude
            self.latitude = latitude
        else:
            self.longitude = None
            self.latitude = None

    def get_distance_to(self, other_address):
        """
        Calculate distance to another address in meters using Haversine formula
        Returns None if either address lacks coordinates
        """
        if self.latitude and self.longitude and other_address.latitude and other_address.longitude:
            lat1, lon1 = float(self.latitude), float(self.longitude)
            lat2, lon2 = float(other_address.latitude), float(other_address.longitude)

            # Haversine formula
            R = 6371000  # Earth's radius in meters
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)

            a = (
                math.sin(delta_phi / 2) * math.sin(delta_phi / 2)
                + math.cos(phi1)
                * math.cos(phi2)
                * math.sin(delta_lambda / 2)
                * math.sin(delta_lambda / 2)
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            return R * c  # Distance in meters
        return None

    def is_within_radius(self, center_lat, center_lon, radius_meters):
        """
        Check if this address is within a given radius of a center point
        """
        if self.latitude and self.longitude:
            # Create a temporary address object for distance calculation
            center_address = Address(latitude=center_lat, longitude=center_lon)
            distance = self.get_distance_to(center_address)
            return distance <= radius_meters if distance is not None else False
        return False

    @property
    def has_coordinates(self):
        """Check if the address has valid coordinates"""
        return self.latitude is not None and self.longitude is not None


class UserProfile(models.Model):
    """
    Extended user profile to store roster ID and other user-specific preferences
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    roster_id = models.CharField(
        max_length=7,
        blank=True,
        default="",
        help_text="Your default roster ID (e.g., DOE1234)",
    )
    drivers_license_id = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Your driver's license ID number",
    )
    home_address = models.TextField(
        blank=True,
        default="",
        help_text="Your home address (street, city, state, zip)",
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_profiles",
        help_text="Your normalized home address",
    )

    # Public profile fields
    public_bio = models.TextField(
        blank=True, default="", help_text="Short public bio"
    )
    public_phone = models.CharField(
        max_length=20, blank=True, default="", help_text="Public phone number"
    )
    public_email = models.EmailField(
        blank=True, default="", help_text="Public email address"
    )
    public_visible = models.BooleanField(
        default=False,
        help_text="Is public profile info visible to org members and incident check-ins?",
    )
    public_bio_visible = models.BooleanField(default=True, help_text="Show bio in public profile")
    public_phone_visible = models.BooleanField(
        default=False, help_text="Show phone in public profile"
    )
    public_email_visible = models.BooleanField(
        default=False, help_text="Show email in public profile"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.roster_id or 'No Roster ID'}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a User is created
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Automatically save the UserProfile when a User is saved
    """
    if hasattr(instance, "profile"):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)
