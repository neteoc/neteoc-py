"""
Unit tests for the operations application forms and views.

Tests cover:
- Form validation
- View authentication and permissions
- View functionality and responses
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import IncidentOrganization, IncidentOrganizationUser
from .forms import IncidentForm, AssetForm


class IncidentFormTest(TestCase):
    """Test cases for the IncidentForm."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="managerpass123",
        )
        self.organization = IncidentOrganization.objects.create(
            name="Test EMS", organization_type="EMS"
        )

    def test_incident_form_valid_data(self):
        """Test incident form with valid data."""
        form_data = {
            "name": "Medical Emergency Response",
            "incident_type": "MEDICAL",
            "status": "ACTIVE",
            "start_date": timezone.now().date(),
            "organization": self.organization.id,
            "incident_commander": self.user.id,
            "description": "Multi-casualty incident response",
        }
        form = IncidentForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_incident_form_invalid_data(self):
        """Test incident form with invalid data."""
        form_data = {
            "name": "",  # Required field left empty
            "incident_type": "INVALID_TYPE",
            "status": "ACTIVE",
        }
        form = IncidentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class AssetFormTest(TestCase):
    """Test cases for the AssetForm."""

    def setUp(self):
        """Set up test data."""
        self.organization = IncidentOrganization.objects.create(
            name="Test Public Works", organization_type="PUBLIC_WORKS"
        )

    def test_asset_form_valid_data(self):
        """Test asset form with valid data."""
        form_data = {
            "identifier": "TRUCK-001",
            "name": "Emergency Response Truck",
            "category": "VEHICLE",
            "organization": self.organization.id,
            "status": "AVAILABLE",
            "description": "Heavy rescue truck with equipment",
            "license_plate": "EMG001",
            "vin": "1HGCM82633A123456",
            "fuel_type": "DIESEL",
        }
        form = AssetForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_asset_form_invalid_identifier(self):
        """Test asset form with invalid identifier."""
        form_data = {
            "identifier": "",  # Required field
            "name": "Test Asset",
            "category": "OTHER",
            "organization": self.organization.id,
            "status": "AVAILABLE",
        }
        form = AssetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("identifier", form.errors)


class OperationsViewTest(TestCase):
    """Test cases for operations views."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.organization = IncidentOrganization.objects.create(
            name="Test Organization", organization_type="OTHER"
        )
        IncidentOrganizationUser.objects.create(
            organization=self.organization, user=self.user, role="ADMIN"
        )

    def test_asset_list_view_requires_login(self):
        """Test that asset list view requires authentication."""
        response = self.client.get(reverse("operations:asset_list"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_asset_list_view_authenticated(self):
        """Test asset list view with authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("operations:asset_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Assets")

    def test_incident_list_view_authenticated(self):
        """Test incident list view with authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("operations:incident_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incidents")

    def test_time_entry_list_view_authenticated(self):
        """Test time entry list view with authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("operations:time_entry_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Time Tracking")
