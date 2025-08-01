from django.urls import path
from . import views

app_name = "user_profile_api"

urlpatterns = [
    path("user/<int:user_id>/roster/", views.UserRosterAPIView.as_view(), name="user_roster"),
]
