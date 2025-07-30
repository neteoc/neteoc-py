from django.db import models

# Create your models here.


class CheckIn(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    roster_id = models.CharField(max_length=7, help_text="Example: DOE1234")
    mileage = models.IntegerField(
        help_text="Round trip miles driven today.Rounded to nearest mile i.e. 123"
    )
    food_expenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Dollar amount spent on food today. i.e. 12.34",
    )
    other_expenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Dollar amount spent on other expenses today. i.e. 64.88",
    )
    expense_notes = models.TextField(
        blank=True, null=True, help_text="Explain any large expenses or unusual mileage."
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    Check_Out = models.BooleanField(
        default=False, help_text="Check this box if you are checking out for the day."
    )
    checkout_time = models.DateTimeField(
        blank=True, null=True, help_text="The time you checked out for the day."
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
