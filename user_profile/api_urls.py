from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "user_profile_api"

# Create a router for ViewSets
router = DefaultRouter()
router.register(r"contacts", views.ContactViewSet, basename="contact")

urlpatterns = [
    # ViewSet routes
    path("", include(router.urls)),
    # Individual API views
    path("user/<int:user_id>/roster/", views.UserRosterAPIView.as_view(), name="user_roster"),
]
