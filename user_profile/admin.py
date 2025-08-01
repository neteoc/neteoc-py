from django.contrib import admin
from .models import UserProfile, Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["street_1", "city", "state", "zip_code", "has_coordinates", "location_accuracy"]
    list_filter = ["state", "location_accuracy"]
    search_fields = ["street_1", "city", "zip_code"]

    def has_coordinates(self, obj):
        """Show if address has coordinate data"""
        return obj.location is not None

    has_coordinates.boolean = True
    has_coordinates.short_description = "Has Coordinates"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "roster_id", "drivers_license_id", "has_address", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "roster_id"]

    def has_address(self, obj):
        """Show if user has address information"""
        return obj.address is not None

    has_address.boolean = True
    has_address.short_description = "Has Address"
