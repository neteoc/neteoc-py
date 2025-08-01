import django_tables2 as tables
from django.utils.html import format_html
from django.urls import reverse
from .models import CheckIn


class CheckInTable(tables.Table):
    checkout = tables.Column(empty_values=(), verbose_name="Action", orderable=False)

    def render_checkout(self, record):
        if record.Check_Out:
            # If already checked out, show the checkout time
            if record.checkout_time:
                return format_html(
                    '<span class="badge bg-success">Checked out at {}</span>',
                    record.checkout_time.strftime("%H:%M"),
                )
            else:
                return format_html('<span class="badge bg-success">Checked out</span>')
        else:
            # If not checked out, show checkout button
            checkout_url = reverse("checkin:checkout", kwargs={"pk": record.pk})
            return format_html(
                '<a href="{}" class="btn btn-sm btn-secondary">Check Out</a>',
                checkout_url,
            )

    class Meta:
        model = CheckIn
        fields = (
            "first_name",
            "last_name",
            "roster_id",
            "mileage",
            "food_expenses",
            "other_expenses",
            "expense_notes",
            "timestamp",
            "checkout",
        )
        attrs = {"class": "table table-striped table-bordered"}
        orderable = True
        sequence = (
            "first_name",
            "last_name",
            "roster_id",
            "mileage",
            "food_expenses",
            "other_expenses",
            "expense_notes",
            "timestamp",
            "checkout",
        )
