from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import (
    Incident,
    CheckIn,
    IncidentOrganization,
    IncidentOrganizationUser,
    IncidentOrganizationOwner,
    IncidentOrganizationInvitation,
    SupportRequest,
    IncidentLink,
    AssetCategory,
    Asset,
    AssetCheckout,
    TimeEntry,
)

# Constants for fieldset names
BASIC_INFORMATION = "Basic Information"
SYSTEM_INFO = "System Info"


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "incident_type",
        "status",
        "organization",
        "start_date",
        "end_date",
        "location",
        "owner",
        "incident_commander",
        "total_checkins_display",
        "active_checkins_display",
        "created_by",
    ]
    list_filter = [
        "status",
        "incident_type",
        "organization",
        "start_date",
        "owner",
        "incident_commander",
        "created_by",
    ]
    search_fields = [
        "name",
        "description",
        "location",
        "owner__username",
        "incident_commander__username",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "total_checkins_display",
        "active_checkins_display",
    ]

    fieldsets = (
        (BASIC_INFORMATION, {"fields": ("name", "incident_type", "description", "status")}),
        ("Organization", {"fields": ("organization",)}),
        ("Dates & Location", {"fields": ("start_date", "end_date", "location")}),
        ("Management", {"fields": ("owner", "incident_commander", "created_by")}),
        (
            "Statistics",
            {
                "fields": ("total_checkins_display", "active_checkins_display"),
                "classes": ("collapse",),
            },
        ),
        (SYSTEM_INFO, {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def total_checkins_display(self, obj):
        """Display total check-ins with link to admin list"""
        count = obj.total_checkins
        if count > 0:
            url = f"/admin/operations/checkin/?incident__id__exact={obj.id}"
            return format_html('<a href="{}">{} check-ins</a>', url, count)
        return "0 check-ins"

    total_checkins_display.short_description = "Total Check-ins"

    def active_checkins_display(self, obj):
        """Display active check-ins with status indicator"""
        count = obj.active_checkins
        if count > 0:
            url = f"/admin/operations/checkin/?incident__id__exact={obj.id}&Check_Out__exact=0"
            return format_html(
                '<a href="{}" style="color: green; font-weight: bold;">{} active</a>', url, count
            )
        return format_html('<span style="color: gray;">0 active</span>')

    active_checkins_display.short_description = "Currently Checked In"

    def save_model(self, request, obj, form, change):
        """Auto-set created_by, owner, and organization to appropriate defaults when creating new incident"""
        if not change:  # Only for new objects
            obj.created_by = request.user
            # If no owner is set, default to current user
            if not obj.owner:
                obj.owner = request.user
            # If no organization is set, try to find user's primary organization
            if not obj.organization:
                try:
                    user_org = IncidentOrganizationUser.objects.filter(user=request.user).first()
                    if user_org:
                        obj.organization = user_org.organization
                    else:
                        # Fallback to Default Organization
                        default_org, _ = IncidentOrganization.objects.get_or_create(
                            name="Default Organization", defaults={"organization_type": "nonprofit"}
                        )
                        obj.organization = default_org
                except Exception:
                    # Final fallback - get any organization
                    obj.organization = IncidentOrganization.objects.first()
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filter incidents based on user's organization access"""
        qs = super().get_queryset(request)

        # Superusers can see all incidents
        if request.user.is_superuser:
            return qs

        # Filter incidents based on organization membership
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        if user_orgs:
            return qs.filter(organization__in=user_orgs)

        # If user is not in any organization, only show incidents they own
        return qs.filter(owner=request.user)

    def has_change_permission(self, request, obj=None):
        """Check if user can change this incident"""
        if not obj:
            return super().has_change_permission(request)

        # Standard Django permission check first
        if not super().has_change_permission(request):
            return False

        # Check incident-specific permissions
        return obj.has_admin_access(request.user)

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete this incident"""
        if not obj:
            return super().has_delete_permission(request)

        # Standard Django permission check first
        if not super().has_delete_permission(request):
            return False

        # Check incident-specific permissions
        return obj.has_admin_access(request.user)


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "roster_id",
        "incident",
        "user",
        "Check_Out",
        "total_expenses",
        "timestamp",
    ]
    list_filter = ["incident", "Check_Out", "timestamp", "incident__status"]
    search_fields = ["first_name", "last_name", "roster_id", "user__username", "incident__name"]
    readonly_fields = ["timestamp", "checkout_time"]

    fieldsets = (
        ("Incident", {"fields": ("incident",)}),
        ("Person Information", {"fields": ("user", "first_name", "last_name", "roster_id")}),
        ("Expenses", {"fields": ("mileage", "food_expenses", "other_expenses", "expense_notes")}),
        ("Check-in/Out", {"fields": ("Check_Out", "timestamp", "checkout_time")}),
    )

    def total_expenses(self, obj):
        """Calculate total expenses for display"""
        return obj.food_expenses + obj.other_expenses

    total_expenses.short_description = "Total Expenses"
    total_expenses.admin_order_field = "food_expenses"

    def get_queryset(self, request):
        """Optimize queryset with select_related and apply organization-based permission filtering"""
        qs = (
            super()
            .get_queryset(request)
            .select_related("incident", "user", "incident__organization")
        )

        # Superusers can see all check-ins
        if request.user.is_superuser:
            return qs

        # Filter based on organization access
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        if user_orgs:
            return qs.filter(incident__organization__in=user_orgs)

        # If user is not in any organization, only show check-ins for incidents they own
        return qs.filter(incident__owner=request.user)

    def has_change_permission(self, request, obj=None):
        """Check if user can change this check-in"""
        if not obj:
            return super().has_change_permission(request)

        # Standard Django permission check first
        if not super().has_change_permission(request):
            return False

        # Check incident-specific permissions
        return obj.incident.has_write_access(request.user)

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete this check-in"""
        if not obj:
            return super().has_delete_permission(request)

        # Standard Django permission check first
        if not super().has_delete_permission(request):
            return False

        # Check incident-specific permissions
        return obj.incident.has_admin_access(request.user)


@admin.register(IncidentOrganization)
class IncidentOrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "organization_type", "is_active", "created"]
    list_filter = ["organization_type", "is_active", "created"]
    search_fields = ["name"]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        (BASIC_INFORMATION, {"fields": ("name", "organization_type", "is_active")}),
        (SYSTEM_INFO, {"fields": ("created", "modified"), "classes": ("collapse",)}),
    )


@admin.register(IncidentOrganizationUser)
class IncidentOrganizationUserAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "is_admin", "created"]
    list_filter = ["role", "is_admin", "organization", "created"]
    search_fields = ["user__username", "user__email", "organization__name"]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        ("User Assignment", {"fields": ("user", "organization", "role", "is_admin")}),
        (SYSTEM_INFO, {"fields": ("created", "modified"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Filter organization users based on user's organization access"""
        qs = super().get_queryset(request).select_related("user", "organization")

        # Superusers can see all organization users
        if request.user.is_superuser:
            return qs

        # Users can only see organization users from organizations they belong to
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(organization__in=user_orgs)


@admin.register(IncidentOrganizationOwner)
class IncidentOrganizationOwnerAdmin(admin.ModelAdmin):
    list_display = ["organization_user", "organization", "created"]
    list_filter = ["organization", "created"]
    search_fields = ["organization_user__user__username", "organization__name"]
    readonly_fields = ["created", "modified"]

    def get_queryset(self, request):
        """Filter organization owners based on user's organization access"""
        qs = super().get_queryset(request).select_related("organization_user__user", "organization")

        # Superusers can see all organization owners
        if request.user.is_superuser:
            return qs

        # Users can only see organization owners from organizations they belong to
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(organization__in=user_orgs)


@admin.register(IncidentOrganizationInvitation)
class IncidentOrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ["invitee_identifier", "organization", "role", "invited_by", "created"]
    list_filter = ["role", "organization", "created"]
    search_fields = ["invitee_identifier", "organization__name", "invited_by__username"]
    readonly_fields = ["guid", "created", "modified"]

    fieldsets = (
        (
            "Invitation Details",
            {"fields": ("invitee_identifier", "organization", "role", "invited_by")},
        ),
        (SYSTEM_INFO, {"fields": ("guid", "created", "modified"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Filter invitations based on user's organization access"""
        qs = super().get_queryset(request).select_related("organization", "invited_by")

        # Superusers can see all invitations
        if request.user.is_superuser:
            return qs

        # Users can only see invitations from organizations they belong to
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(organization__in=user_orgs)


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "requesting_organization",
        "target_organization",
        "status",
        "urgency",
        "requested_by",
        "reviewed_by",
        "created_at",
    ]
    list_filter = [
        "status",
        "urgency",
        "requesting_organization",
        "target_organization",
        "created_at",
    ]
    search_fields = [
        "title",
        "description",
        "requesting_organization__name",
        "target_organization__name",
        "requested_by__username",
    ]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]

    fieldsets = (
        ("Request Details", {"fields": ("title", "description", "urgency")}),
        ("Organizations", {"fields": ("requesting_organization", "target_organization")}),
        ("Related Incident", {"fields": ("related_incident",)}),
        ("Timing", {"fields": ("requested_start_date", "requested_end_date")}),
        ("Management", {"fields": ("requested_by", "reviewed_by", "status")}),
        ("Response", {"fields": ("response_notes", "approved_resources")}),
        (
            SYSTEM_INFO,
            {"fields": ("created_at", "updated_at", "reviewed_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Filter support requests based on user's organization access"""
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "requesting_organization", "target_organization", "related_incident", "requested_by"
            )
        )

        # Superusers can see all support requests
        if request.user.is_superuser:
            return qs

        # Users can see requests involving their organizations
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(
            models.Q(requesting_organization__in=user_orgs)
            | models.Q(target_organization__in=user_orgs)
        )

    def save_model(self, request, obj, form, change):
        """Auto-set requested_by when creating new support request"""
        if not change:  # Only for new objects
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(IncidentLink)
class IncidentLinkAdmin(admin.ModelAdmin):
    list_display = [
        "from_incident",
        "relationship_type",
        "to_incident",
        "created_by",
        "created_at",
    ]
    list_filter = [
        "relationship_type",
        "from_incident__organization",
        "to_incident__organization",
        "created_at",
    ]
    search_fields = [
        "from_incident__name",
        "to_incident__name",
        "notes",
        "created_by__username",
    ]
    readonly_fields = ["created_at"]

    fieldsets = (
        (
            "Incident Relationship",
            {"fields": ("from_incident", "relationship_type", "to_incident")},
        ),
        ("Details", {"fields": ("notes", "created_by")}),
        (SYSTEM_INFO, {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Filter incident links based on user's organization access"""
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "from_incident",
                "to_incident",
                "from_incident__organization",
                "to_incident__organization",
            )
        )

        # Superusers can see all incident links
        if request.user.is_superuser:
            return qs

        # Users can see links involving incidents from their organizations
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(
            models.Q(from_incident__organization__in=user_orgs)
            | models.Q(to_incident__organization__in=user_orgs)
        )

    def save_model(self, request, obj, form, change):
        """Auto-set created_by when creating new incident link"""
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Asset Management Admin


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "requires_license", "requires_training", "created_at"]
    list_filter = ["requires_license", "requires_training", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Category Information", {"fields": ("name", "description")}),
        ("Requirements", {"fields": ("requires_license", "requires_training")}),
        (SYSTEM_INFO, {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        "identifier",
        "name",
        "category",
        "organization",
        "status",
        "current_holder",
        "current_incident",
        "created_at",
    ]
    list_filter = [
        "status",
        "category",
        "organization",
        "current_incident",
        "created_at",
    ]
    search_fields = [
        "identifier",
        "name",
        "description",
        "serial_number",
        "license_plate",
        "call_sign",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (BASIC_INFORMATION, {"fields": ("identifier", "name", "description", "category")}),
        (
            "Ownership & Location",
            {"fields": ("organization", "current_holder", "current_incident")},
        ),
        ("Status & Location", {"fields": ("status", "location")}),
        (
            "Asset Details",
            {
                "fields": (
                    "serial_number",
                    "purchase_date",
                    "warranty_expiration",
                    "value",
                )
            },
        ),
        (
            "Radio-Specific",
            {"fields": ("frequency", "call_sign"), "classes": ("collapse",)},
        ),
        (
            "Vehicle-Specific",
            {"fields": ("license_plate", "vin", "fuel_type"), "classes": ("collapse",)},
        ),
        (SYSTEM_INFO, {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Filter assets based on user's organization access"""
        qs = (
            super()
            .get_queryset(request)
            .select_related("category", "organization", "current_holder", "current_incident")
        )

        # Superusers can see all assets
        if request.user.is_superuser:
            return qs

        # Filter assets based on organization membership
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(organization__in=user_orgs)

    def has_change_permission(self, request, obj=None):
        """Check if user can change this asset"""
        if not obj:
            return super().has_change_permission(request)

        # Standard Django permission check first
        if not super().has_change_permission(request):
            return False

        # Check asset-specific permissions
        return obj.can_user_manage(request.user)

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete this asset"""
        if not obj:
            return super().has_delete_permission(request)

        # Standard Django permission check first
        if not super().has_delete_permission(request):
            return False

        # Check asset-specific permissions
        return obj.can_user_manage(request.user)


@admin.register(AssetCheckout)
class AssetCheckoutAdmin(admin.ModelAdmin):
    list_display = [
        "asset",
        "checked_out_by",
        "checked_out_to",
        "incident",
        "status",
        "checkout_time",
        "accepted_time",
        "checkin_time",
    ]
    list_filter = [
        "status",
        "asset__category",
        "asset__organization",
        "incident",
        "checkout_time",
    ]
    search_fields = [
        "asset__identifier",
        "asset__name",
        "checked_out_by__username",
        "checked_out_to__username",
        "purpose",
    ]
    readonly_fields = ["checkout_time", "accepted_time", "checkin_time"]

    fieldsets = (
        ("Checkout Details", {"fields": ("asset", "checked_out_by", "checked_out_to")}),
        ("Purpose & Incident", {"fields": ("incident", "purpose")}),
        (
            "Status & Timing",
            {"fields": ("status", "checkout_time", "accepted_time", "checkin_time")},
        ),
        (
            "Condition Tracking",
            {
                "fields": (
                    "checkout_condition",
                    "checkin_condition",
                    "issues_reported",
                )
            },
        ),
        (
            "Location Tracking",
            {"fields": ("checkout_location", "checkin_location")},
        ),
    )

    def get_queryset(self, request):
        """Filter asset checkouts based on user's organization access"""
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "asset",
                "asset__organization",
                "checked_out_by",
                "checked_out_to",
                "incident",
            )
        )

        # Superusers can see all checkouts
        if request.user.is_superuser:
            return qs

        # Filter based on organization access
        user_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
            "organization", flat=True
        )
        return qs.filter(asset__organization__in=user_orgs)

    def has_change_permission(self, request, obj=None):
        """Check if user can change this asset checkout"""
        if not obj:
            return super().has_change_permission(request)

        # Standard Django permission check first
        if not super().has_change_permission(request):
            return False

        # Users involved in the checkout can change it
        if request.user in [obj.checked_out_by, obj.checked_out_to]:
            return True

        # Asset managers can change checkouts
        return obj.asset.can_user_manage(request.user)

    def has_delete_permission(self, request, obj=None):
        """Check if user can delete this asset checkout"""
        if not obj:
            return super().has_delete_permission(request)

        # Standard Django permission check first
        if not super().has_delete_permission(request):
            return False

        # Only asset managers can delete checkouts
        return obj.asset.can_user_manage(request.user)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "organization",
        "date",
        "total_hours_display",
        "total_costs_display",
        "incident",
        "activity_description_short",
    ]
    list_filter = [
        "organization",
        "date",
        "user",
        "incident",
    ]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "organization__name",
        "activity_description",
    ]
    readonly_fields = ["created_at", "updated_at", "total_hours_display", "total_costs_display"]
    
    fieldsets = [
        (BASIC_INFORMATION, {
            "fields": ("user", "organization", "incident", "date", "activity_description")
        }),
        ("Time Tracking", {
            "fields": ("work_hours", "volunteer_hours", "travel_hours", "travel_miles")
        }),
        ("Cost Tracking", {
            "fields": ("travel_meal_costs", "billeting_costs", "purchases", "purchase_explanation")
        }),
        ("Summary", {
            "fields": ("total_hours_display", "total_costs_display"),
            "classes": ("collapse",)
        }),
        (SYSTEM_INFO, {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    ]
    
    def get_queryset(self, request):
        """Filter time entries by organization membership"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        
        # Filter to organizations the user is a member of
        user_orgs = IncidentOrganization.objects.filter(
            users=request.user
        ).values_list('pk', flat=True)
        return qs.filter(organization__in=user_orgs)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit organization choices to user's organizations"""
        if db_field.name == "organization" and not request.user.is_superuser:
            kwargs["queryset"] = IncidentOrganization.objects.filter(users=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def total_hours_display(self, obj):
        """Display total hours"""
        return f"{obj.total_hours:.2f}"
    total_hours_display.short_description = "Total Hours"
    
    def total_costs_display(self, obj):
        """Display total costs"""
        return f"${obj.total_costs:.2f}"
    total_costs_display.short_description = "Total Costs"
    
    def activity_description_short(self, obj):
        """Display truncated activity description"""
        return obj.activity_description[:50] + "..." if len(obj.activity_description) > 50 else obj.activity_description
    activity_description_short.short_description = "Activity"
    
    def has_view_permission(self, request, obj=None):
        """Users can view time entries for their organizations"""
        if not super().has_view_permission(request):
            return False
        
        if obj is None:
            return True
        
        if request.user.is_superuser:
            return True
        
        # Check if user is member of the organization
        return obj.organization.users.filter(pk=request.user.pk).exists()
    
    def has_change_permission(self, request, obj=None):
        """Users can only edit their own time entries"""
        if not super().has_change_permission(request):
            return False
        
        if obj is None:
            return True
        
        if request.user.is_superuser:
            return True
        
        # Users can only edit their own time entries
        return obj.user == request.user
    
    def has_delete_permission(self, request, obj=None):
        """Users can only delete their own time entries"""
        if not super().has_delete_permission(request):
            return False
        
        if obj is None:
            return True
        
        if request.user.is_superuser:
            return True
        
        # Users can only delete their own time entries
        return obj.user == request.user
