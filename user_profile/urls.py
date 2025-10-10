from django.urls import path, include
from . import views

app_name = "user_profile"

urlpatterns = [
    # Web interface URLs
    path("", views.profile, name="profile"),
    path("public/edit/", views.edit_public_profile, name="public_profile_edit"),
    path("public/<int:user_id>/", views.view_public_profile, name="public_profile_view"),
    # Contact management URLs
    path("contacts/", views.contact_list, name="contact_list"),
    path("contacts/create/", views.contact_create, name="contact_create"),
    path("contacts/<int:contact_id>/edit/", views.contact_edit, name="contact_edit"),
    path("contacts/<int:contact_id>/delete/", views.contact_delete, name="contact_delete"),
    path("contacts/<int:contact_id>/detail/", views.contact_detail, name="contact_detail"),
    # API URLs (versioned)
    path("api/", include("user_profile.api_urls")),
]
