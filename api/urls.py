"""
API URL configuration for NetEOC project

This module provides versioned API endpoints for all applications.
Current API version: v1

Security Features:
- All endpoints require authentication
- Rate limiting applied
- Consistent error handling
- Logging of all API access
"""

from django.urls import path, include
from . import views

app_name = "api"

# API version 1 URLs
v1_patterns = [
    path("", views.APIv1RootView.as_view(), name="v1_root"),
    path("user-profile/", include("user_profile.api_urls")),
    # Future: path("operations/", include("operations.api_urls")),
    # Future: path("reports/", include("reports.api_urls")),
]

urlpatterns = [
    path("", views.APIRootView.as_view(), name="root"),
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
