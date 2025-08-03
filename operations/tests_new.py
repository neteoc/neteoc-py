"""
Test discovery for the operations application.

This module provides a single entry point for all tests in the operations app.
Test classes are organized in separate modules for better maintainability:

- test_models.py: Model functionality tests
- test_forms_views.py: Form validation and view tests
"""

# Import all test classes for test discovery
from .test_models import (
    IncidentOrganizationModelTest,
    IncidentModelTest,
    AssetModelTest,
    TimeEntryModelTest,
    SupportRequestModelTest,
    CheckInModelTest,
    PermissionsTest,
)

from .test_forms_views import (
    IncidentFormTest,
    AssetFormTest,
    OperationsViewTest,
)

__all__ = [
    "IncidentOrganizationModelTest",
    "IncidentModelTest",
    "AssetModelTest",
    "TimeEntryModelTest",
    "SupportRequestModelTest",
    "CheckInModelTest",
    "PermissionsTest",
    "IncidentFormTest",
    "AssetFormTest",
    "OperationsViewTest",
]
