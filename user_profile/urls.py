from django.urls import path, include
from . import views

app_name = "user_profile"

urlpatterns = [
    # Web interface URLs
    path("", views.profile, name="profile"),
    path("public/edit/", views.edit_public_profile, name="public_profile_edit"),
    path("public/<int:user_id>/", views.view_public_profile, name="public_profile_view"),
    # API URLs (versioned)
    path("api/", include("user_profile.api_urls")),
]
