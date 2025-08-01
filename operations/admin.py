from django.contrib import admin
from django.utils.html import format_html
from .models import Incident, CheckIn


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "incident_type",
        "status",
        "start_date",
        "end_date",
        "location",
        "owner",
        "total_checkins_display",
        "active_checkins_display",
        "created_by",
    ]
    list_filter = ["status", "incident_type", "start_date", "owner", "created_by"]
    search_fields = ["name", "description", "location", "owner__username"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "total_checkins_display",
        "active_checkins_display",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "incident_type", "description", "status")}),
        ("Dates & Location", {"fields": ("start_date", "end_date", "location")}),
        ("Management", {"fields": ("owner", "created_by")}),
        (
            "Statistics",
            {
                "fields": ("total_checkins_display", "active_checkins_display"),
                "classes": ("collapse",),
            },
        ),
        ("System Info", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
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
        """Auto-set created_by and owner to current user when creating new incident"""
        if not change:  # Only for new objects
            obj.created_by = request.user
            # If no owner is set, default to current user
            if not obj.owner:
                obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filter incidents based on user permissions"""
        qs = super().get_queryset(request)

        # Superusers and staff can see all incidents
        if request.user.is_superuser or request.user.is_staff:
            return qs

        # Users can see incidents they own, or incidents they have group access to
        from django.db.models import Q

        # Start with incidents user owns
        user_filter = Q(owner=request.user)

        # Add incidents user has access to via groups
        if request.user.groups.filter(
            name__in=["Incident Admins", "Incident Responders", "Incident Viewers"]
        ).exists():
            # Users in these groups can see all incidents
            return qs

        return qs.filter(user_filter)

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
        """Optimize queryset with select_related and apply permission filtering"""
        qs = super().get_queryset(request).select_related("incident", "user")

        # Superusers and staff can see all check-ins
        if request.user.is_superuser or request.user.is_staff:
            return qs

        # Filter based on incident access
        from django.db.models import Q

        # Users can see check-ins for incidents they have access to
        incident_filter = Q(incident__owner=request.user)

        # Add incidents user has access to via groups
        if request.user.groups.filter(
            name__in=["Incident Admins", "Incident Responders", "Incident Viewers"]
        ).exists():
            # Users in these groups can see all check-ins
            return qs

        return qs.filter(incident_filter)

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
