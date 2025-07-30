from django.contrib import admin
from .models import CheckIn

# Register your models here.


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "mileage",
        "food_expenses",
        "other_expenses",
        "expense_notes",
        "timestamp",
        "Check_Out",
        "checkout_time",
    )
    list_filter = ("timestamp",)
    search_fields = ("first_name", "last_name")
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp",)
