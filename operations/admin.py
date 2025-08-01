from django.contrib import admin
from .models import CheckIn


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "roster_id",
        "user",
        "Check_Out",
        "total_expenses",
        "timestamp",
    ]
    list_filter = ["Check_Out", "timestamp"]
    search_fields = ["first_name", "last_name", "roster_id", "user__username"]
    readonly_fields = ["timestamp", "checkout_time"]

    def total_expenses(self, obj):
        """Calculate total expenses for display"""
        return obj.food_expenses + obj.other_expenses

    total_expenses.short_description = "Total Expenses"
    total_expenses.admin_order_field = "food_expenses"
