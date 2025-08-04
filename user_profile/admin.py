from django.contrib import admin
from .models import UserProfile, Address, Contact


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["street_1", "city", "state", "zip_code", "has_coordinates", "location_accuracy"]
    list_filter = ["state", "location_accuracy"]
    search_fields = ["street_1", "city", "zip_code"]

    def has_coordinates(self, obj):
        """Show if address has coordinate data"""
        return obj.has_coordinates

    has_coordinates.boolean = True
    has_coordinates.short_description = "Has Coordinates"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "roster_id",
        "drivers_license_id",
        "has_address",
        "use_gravatar",
        "created_at",
    ]
    list_filter = ["created_at", "use_gravatar", "public_visible"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "roster_id"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "roster_id", "drivers_license_id")}),
        ("Address Information", {"fields": ("home_address", "address"), "classes": ("collapse",)}),
        (
            "Public Profile",
            {
                "fields": (
                    "public_visible",
                    "public_bio",
                    "public_bio_visible",
                    "public_phone",
                    "public_phone_visible",
                    "public_email",
                    "public_email_visible",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Profile Photo",
            {
                "fields": ("use_gravatar", "gravatar_email"),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def has_address(self, obj):
        """Show if user has address information"""
        return obj.address is not None

    has_address.boolean = True
    has_address.short_description = "Has Address"


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "contact_type",
        "value",
        "organization",
        "is_primary",
        "is_active",
        "created_at",
    ]
    list_filter = ["contact_type", "is_primary", "is_active", "created_at"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "value"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Contact Information", {"fields": ("user", "contact_type", "value", "organization")}),
        ("Settings", {"fields": ("is_primary", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("user", "organization")
