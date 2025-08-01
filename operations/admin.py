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
        "total_checkins_display",
        "active_checkins_display",
        "created_by",
    ]
    list_filter = ["status", "incident_type", "start_date", "created_by"]
    search_fields = ["name", "description", "location"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "total_checkins_display",
        "active_checkins_display",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "incident_type", "description", "status")}),
        ("Dates & Location", {"fields": ("start_date", "end_date", "location")}),
        ("Management", {"fields": ("created_by",)}),
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
        """Auto-set created_by to current user when creating new incident"""
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


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
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("incident", "user")
