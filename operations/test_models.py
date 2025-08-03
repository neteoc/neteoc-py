"""
Unit tests for the operations application models.

Tests cover core model functionality including:
- Organization management
- Incident creation and management
- Asset tracking
- Time tracking
- Support requests
- Check-in/check-out functionality
"""

import secrets
import string
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    IncidentOrganization,
    IncidentOrganizationUser,
    Incident,
    AssetCategory,
    Asset,
    TimeEntry,
    SupportRequest,
    CheckIn,
)


# Password generation utility
def generate_test_password():
    """Generate a random password for test purposes."""
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))


# Test password constants
TEST_PASSWORD_1 = generate_test_password()
TEST_PASSWORD_2 = generate_test_password()
TEST_PASSWORD_3 = generate_test_password()
TEST_PASSWORD_4 = generate_test_password()
TEST_PASSWORD_5 = generate_test_password()
TEST_PASSWORD_6 = generate_test_password()
TEST_PASSWORD_7 = generate_test_password()
TEST_PASSWORD_8 = generate_test_password()
TEST_PASSWORD_9 = generate_test_password()
TEST_PASSWORD_10 = generate_test_password()


class IncidentOrganizationModelTest(TestCase):
    """Test cases for the IncidentOrganization model."""

    def setUp(self):
        """Set up test data."""
        self.organization = IncidentOrganization.objects.create(
            name="Test Fire Department",
            organization_type="FIRE",
            contact_email="contact@testfire.gov",
            contact_phone="555-0123",
            address="123 Main St, Test City, TS 12345",
            is_verified=True,
        )

    def test_organization_creation(self):
        """Test organization model creation and string representation."""
        expected_str = "Test Fire Department (Fire Department)"
        self.assertEqual(str(self.organization), expected_str)
        self.assertEqual(self.organization.organization_type, "FIRE")
        self.assertTrue(self.organization.is_verified)
        contact_email = "contact@testfire.gov"
        self.assertEqual(self.organization.contact_email, contact_email)

    def test_organization_type_choices(self):
        """Test that organization type choices are properly defined."""
        choices = dict(IncidentOrganization.ORGANIZATION_TYPES)
        self.assertIn("FIRE", choices)
        self.assertIn("POLICE", choices)
        self.assertIn("EMS", choices)
        self.assertEqual(choices["FIRE"], "Fire Department")


class IncidentModelTest(TestCase):
    """Test cases for the Incident model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password=TEST_PASSWORD_1,
        )
        self.organization = IncidentOrganization.objects.create(
            name="Test Emergency Management",
            organization_type="EMERGENCY_MGMT",
        )
        self.incident = Incident.objects.create(
            name="Test Hurricane Response",
            incident_type="HURRICANE",
            status="ACTIVE",
            start_date=timezone.now(),
            organization=self.organization,
            owner=self.user,
            incident_commander=self.user,
        )

    def test_incident_creation(self):
        """Test incident model creation and basic properties."""
        expected_str = "Test Hurricane Response (Hurricane)"
        self.assertEqual(str(self.incident), expected_str)
        self.assertEqual(self.incident.incident_type, "HURRICANE")
        self.assertEqual(self.incident.status, "ACTIVE")
        self.assertEqual(self.incident.owner, self.user)
        self.assertEqual(self.incident.incident_commander, self.user)

    def test_incident_has_admin_access(self):
        """Test incident admin access permissions."""
        # Owner should have admin access
        self.assertTrue(self.incident.has_admin_access(self.user))

        # Non-owner should not have admin access
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password=TEST_PASSWORD_2,
        )
        self.assertFalse(self.incident.has_admin_access(other_user))

        # Superuser should have admin access
        superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=TEST_PASSWORD_3,
        )
        self.assertTrue(self.incident.has_admin_access(superuser))

    def test_incident_has_read_access(self):
        """Test incident read access permissions."""
        # Owner should have read access
        self.assertTrue(self.incident.has_read_access(self.user))

        # Create organization membership for read access test
        other_user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password=TEST_PASSWORD_4,
        )
        IncidentOrganizationUser.objects.create(
            organization=self.organization, user=other_user, role="MEMBER"
        )
        self.assertTrue(self.incident.has_read_access(other_user))


class AssetModelTest(TestCase):
    """Test cases for the Asset model."""

    def setUp(self):
        """Set up test data."""
        self.organization = IncidentOrganization.objects.create(
            name="Test Police Department", organization_type="POLICE"
        )
        self.asset_category = AssetCategory.objects.create(
            name="Radio",
            description="Radio communication equipment",
            requires_license=True,
            requires_training=False,
        )
        self.asset = Asset.objects.create(
            identifier="RADIO-001",
            name="Motorola Radio",
            category=self.asset_category,
            organization=self.organization,
            status="AVAILABLE",
            serial_number="MOT123456",
            value=Decimal("750.00"),
            frequency="155.475",
            call_sign="KD8ABC",
        )

    def test_asset_creation(self):
        """Test asset model creation and properties."""
        self.assertEqual(str(self.asset), "RADIO-001 - Motorola Radio")
        self.assertEqual(self.asset.category.name, "Radio")
        self.assertEqual(self.asset.status, "AVAILABLE")
        self.assertEqual(self.asset.value, Decimal("750.00"))
        self.assertEqual(self.asset.frequency, "155.475")

    def test_asset_availability_status(self):
        """Test asset availability status changes."""
        self.assertTrue(self.asset.is_available)
        self.asset.status = "IN_USE"
        self.asset.save()
        self.assertFalse(self.asset.is_available)


class TimeEntryModelTest(TestCase):
    """Test cases for the TimeEntry model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="volunteer",
            email="volunteer@example.com",
            password=TEST_PASSWORD_5,
        )
        self.organization = IncidentOrganization.objects.create(
            name="Test Volunteer Group", organization_type="VOLUNTEER"
        )
        self.time_entry = TimeEntry.objects.create(
            user=self.user,
            organization=self.organization,
            date=date.today(),
            activity_description="Emergency response training",
            work_hours=Decimal("8.00"),
            volunteer_hours=Decimal("2.00"),
            travel_hours=Decimal("1.50"),
            travel_miles=50,
            travel_meal_costs=Decimal("25.00"),
            billeting_costs=Decimal("0.00"),
            purchases=Decimal("15.50"),
            purchase_explanation="First aid supplies",
        )

    def test_time_entry_creation(self):
        """Test time entry model creation and calculations."""
        expected_str = f"volunteer - Test Volunteer Group - {date.today()}"
        self.assertEqual(str(self.time_entry), expected_str)
        self.assertEqual(self.time_entry.work_hours, Decimal("8.00"))
        self.assertEqual(self.time_entry.volunteer_hours, Decimal("2.00"))
        self.assertEqual(self.time_entry.travel_miles, 50)

    def test_time_entry_total_costs(self):
        """Test time entry total cost calculation."""
        expected_total = Decimal("25.00") + Decimal("0.00") + Decimal("15.50")
        actual_total = (
            self.time_entry.travel_meal_costs
            + self.time_entry.billeting_costs
            + self.time_entry.purchases
        )
        self.assertEqual(actual_total, expected_total)


class SupportRequestModelTest(TestCase):
    """Test cases for the SupportRequest model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="coordinator",
            email="coord@example.com",
            password=TEST_PASSWORD_6,
        )
        self.requesting_org = IncidentOrganization.objects.create(
            name="City Emergency Management",
            organization_type="EMERGENCY_MGMT",
        )
        self.target_org = IncidentOrganization.objects.create(
            name="State Defense Force", organization_type="STATE"
        )
        self.incident = Incident.objects.create(
            name="Flood Response 2025",
            incident_type="FLOOD",
            status="ACTIVE",
            start_date=timezone.now(),
            organization=self.requesting_org,
            owner=self.user,
        )
        self.support_request = SupportRequest.objects.create(
            requested_by=self.user,
            requesting_organization=self.requesting_org,
            target_organization=self.target_org,
            related_incident=self.incident,
            title="Emergency Communications Support",
            description="Need radio operators for EOC",
            requested_start_date=timezone.now(),
            requested_end_date=(timezone.now() + timedelta(days=7)),
            urgency="HIGH",
            status="PENDING",
        )

    def test_support_request_creation(self):
        """Test support request model creation."""
        expected_str = (
            "Emergency Communications Support - City Emergency Management → State Defense Force"
        )
        self.assertEqual(str(self.support_request), expected_str)
        self.assertEqual(self.support_request.status, "PENDING")
        self.assertEqual(self.support_request.urgency, "HIGH")
        title = "Emergency Communications Support"
        self.assertEqual(self.support_request.title, title)

    def test_support_request_status_workflow(self):
        """Test support request status transitions."""
        self.assertEqual(self.support_request.status, "PENDING")
        self.support_request.status = "APPROVED"
        self.support_request.save()
        self.assertEqual(self.support_request.status, "APPROVED")


class CheckInModelTest(TestCase):
    """Test cases for the CheckIn model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="responder",
            email="responder@example.com",
            password=TEST_PASSWORD_7,
        )
        self.organization = IncidentOrganization.objects.create(
            name="Test Fire Department", organization_type="FIRE"
        )
        self.incident = Incident.objects.create(
            name="Structure Fire Response",
            incident_type="FIRE",
            status="ACTIVE",
            start_date=timezone.now(),
            organization=self.organization,
            owner=self.user,
        )
        self.checkin = CheckIn.objects.create(
            incident=self.incident,
            first_name="John",
            last_name="Doe",
            roster_id="FD001",
            mileage=50,
            food_expenses=Decimal("25.00"),
            other_expenses=Decimal("10.00"),
            user=self.user,
        )

    def test_checkin_creation(self):
        """Test check-in model creation."""
        expected_str = "John Doe - Structure Fire Response"
        self.assertEqual(str(self.checkin), expected_str)
        self.assertEqual(self.checkin.roster_id, "FD001")
        self.assertEqual(self.checkin.mileage, 50)
        self.assertFalse(self.checkin.Check_Out)

    def test_checkin_checkout_workflow(self):
        """Test check-in/check-out workflow."""
        self.assertFalse(self.checkin.Check_Out)
        self.checkin.Check_Out = True
        self.checkin.checkout_time = timezone.now()
        self.checkin.save()
        self.assertTrue(self.checkin.Check_Out)


class PermissionsTest(TestCase):
    """Test cases for permissions and access control."""

    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password=TEST_PASSWORD_8,
        )
        self.member_user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password=TEST_PASSWORD_9,
        )
        self.outsider_user = User.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password=TEST_PASSWORD_10,
        )

        self.organization = IncidentOrganization.objects.create(
            name="Secure Organization", organization_type="FEDERAL"
        )

        # Create organization memberships
        IncidentOrganizationUser.objects.create(
            organization=self.organization, user=self.admin_user, role="ADMIN"
        )
        IncidentOrganizationUser.objects.create(
            organization=self.organization,
            user=self.member_user,
            role="MEMBER",
        )

        self.incident = Incident.objects.create(
            name="Classified Operation",
            incident_type="OTHER",
            status="ACTIVE",
            start_date=timezone.now(),
            organization=self.organization,
            owner=self.admin_user,
        )

    def test_organization_member_access(self):
        """Test that organization members have appropriate access."""
        self.assertTrue(self.incident.has_read_access(self.admin_user))
        self.assertTrue(self.incident.has_read_access(self.member_user))
        self.assertFalse(self.incident.has_read_access(self.outsider_user))

    def test_admin_permissions(self):
        """Test that admin users have elevated permissions."""
        self.assertTrue(self.incident.has_admin_access(self.admin_user))
        self.assertFalse(self.incident.has_admin_access(self.member_user))
        self.assertFalse(self.incident.has_admin_access(self.outsider_user))
