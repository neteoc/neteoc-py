from django.urls import path, include
from . import views

app_name = "user_profile"

urlpatterns = [
    # Web interface URLs
    path("", views.profile, name="profile"),
    # API URLs (versioned)
    path("api/", include("user_profile.api_urls")),
]
