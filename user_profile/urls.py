from django.urls import path
from . import views

app_name = "user_profile"

urlpatterns = [
    path("", views.profile, name="profile"),
    path("api/user/<int:user_id>/roster/", views.get_user_roster_id, name="user_roster_api"),
]
