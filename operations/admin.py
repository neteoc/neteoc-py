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
)


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
        ("Basic Information", {"fields": ("name", "incident_type", "description", "status")}),
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
        ("Basic Information", {"fields": ("name", "organization_type", "is_active")}),
        ("System Info", {"fields": ("created", "modified"), "classes": ("collapse",)}),
    )


@admin.register(IncidentOrganizationUser)
class IncidentOrganizationUserAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "is_admin", "created"]
    list_filter = ["role", "is_admin", "organization", "created"]
    search_fields = ["user__username", "user__email", "organization__name"]
    readonly_fields = ["created", "modified"]

    fieldsets = (
        ("User Assignment", {"fields": ("user", "organization", "role", "is_admin")}),
        ("System Info", {"fields": ("created", "modified"), "classes": ("collapse",)}),
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
        ("System Info", {"fields": ("guid", "created", "modified"), "classes": ("collapse",)}),
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
            "System Info",
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
        ("System Info", {"fields": ("created_at",), "classes": ("collapse",)}),
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
