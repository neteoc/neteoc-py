from django.contrib import admin
from .models import CheckIn, UserProfile, Address

# Register your models here.


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "street_1",
        "city",
        "state",
        "zip_code",
        "has_coordinates",
        "location_accuracy",
        "created_at",
    )
    list_filter = ("state", "city", "location_accuracy", "created_at")
    search_fields = ("street_1", "street_2", "city", "state", "zip_code")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "geocoded_at")

    fieldsets = (
        ("Address Information", {"fields": ("street_1", "street_2", "city", "state", "zip_code")}),
        (
            "Geographic Information",
            {
                "fields": ("latitude", "longitude", "location_accuracy"),
                "description": "Coordinates in WGS84 format (latitude, longitude)",
            },
        ),
        (
            "Geocoding Metadata",
            {
                "fields": ("geocoded_at", "geocoding_source"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_coordinates(self, obj):
        """Show if the address has coordinates"""
        return obj.has_coordinates

    has_coordinates.boolean = True
    has_coordinates.short_description = "Has Coordinates"


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "user",
        "roster_id",
        "mileage",
        "food_expenses",
        "other_expenses",
        "expense_notes",
        "timestamp",
        "Check_Out",
        "checkout_time",
    )
    list_filter = ("timestamp", "Check_Out", "user")
    search_fields = ("first_name", "last_name", "roster_id", "user__username")
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "roster_id", "drivers_license_id", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "roster_id",
        "drivers_license_id",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    fields = ("user", "roster_id", "drivers_license_id", "home_address", "created_at", "updated_at")
