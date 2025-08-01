from django.contrib import admin
from .models import CheckIn, UserProfile

# Register your models here.


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
    list_display = ("user", "roster_id", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "roster_id")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
