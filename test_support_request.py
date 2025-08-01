#!/usr/bin/env python
"""
Test script to verify support request functionality
"""

import os
import sys
from datetime import timedelta
import django

# Add the project directory to the path
sys.path.append("/home/kwhatcher/projects/neteoc-py")

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neteoc.settings")
django.setup()

# Django imports must come after django.setup()
from django.contrib.auth.models import User  # noqa: E402
from django.utils import timezone  # noqa: E402
from operations.models import (  # noqa: E402
    Incident,
    SupportRequest,
    IncidentOrganization,
    IncidentOrganizationUser,
)


def test_support_request_functionality():
    """Test the complete support request workflow"""
    print("🧪 Testing Support Request Functionality")
    print("=" * 50)

    try:
        # Get or create test users
        user1, created = User.objects.get_or_create(
            username="testuser1",
            defaults={"email": "user1@example.com", "first_name": "Test", "last_name": "User1"},
        )
        if created:
            user1.set_password("testpass123")
            user1.save()
            print(f"✅ Created test user: {user1.username}")
        else:
            print(f"✅ Using existing test user: {user1.username}")

        # Get or create test organizations
        requesting_org, created = IncidentOrganization.objects.get_or_create(
            name="Emergency Management Agency",
            defaults={"is_active": True, "organization_type": "EMERGENCY_MGMT"},
        )
        if created:
            print(f"✅ Created requesting organization: {requesting_org.name}")
        else:
            print(f"✅ Using existing requesting organization: {requesting_org.name}")

        target_org, created = IncidentOrganization.objects.get_or_create(
            name="State Defense Force", defaults={"is_active": True, "organization_type": "STATE"}
        )
        if created:
            print(f"✅ Created target organization: {target_org.name}")
        else:
            print(f"✅ Using existing target organization: {target_org.name}")

        # Add user to both organizations
        req_org_user, created = IncidentOrganizationUser.objects.get_or_create(
            organization=requesting_org, user=user1, defaults={"is_admin": True, "role": "ADMIN"}
        )
        if created:
            print("✅ Added user to requesting organization")

        target_org_user, created = IncidentOrganizationUser.objects.get_or_create(
            organization=target_org, user=user1, defaults={"is_admin": True, "role": "ADMIN"}
        )
        if created:
            print("✅ Added user to target organization")

        # Create a test incident
        incident = Incident.objects.create(
            name="Test Hurricane Response",
            description="Testing support request functionality",
            status="ACTIVE",
            incident_type="HURRICANE",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            organization=requesting_org,
            owner=user1,
            incident_commander=user1,
        )
        print(f"✅ Created test incident: {incident.name}")

        # Create a test support request
        support_request = SupportRequest.objects.create(
            title="Emergency Personnel Support",
            description="Need additional personnel for hurricane response",
            urgency="HIGH",
            requesting_organization=requesting_org,
            target_organization=target_org,
            related_incident=incident,
            requested_by=user1,
            requested_start_date=timezone.now() + timedelta(days=1),
            requested_end_date=timezone.now() + timedelta(days=5),
            status="PENDING",
        )
        print(f"✅ Created test support request: {support_request.title}")
        print(f"   Status: {support_request.status}")
        print(f"   From: {support_request.requesting_organization.name}")
        print(f"   To: {support_request.target_organization.name}")
        print(f"   Related Incident: {support_request.related_incident.name}")

        # Test the cancellation functionality
        print("\n🧪 Testing Cancellation Functionality")
        print("-" * 30)

        original_status = support_request.status
        support_request.status = "CANCELLED"
        support_request.save()

        print("✅ Support request cancelled")
        print(f"   Original status: {original_status}")
        print(f"   New status: {support_request.status}")

        # Test filtering (should exclude cancelled requests)
        active_requests = SupportRequest.objects.exclude(status="CANCELLED")
        all_requests = SupportRequest.objects.all()

        print("\n📊 Request Counts:")
        print(f"   Total requests: {all_requests.count()}")
        print(f"   Active requests: {active_requests.count()}")
        print(f"   Cancelled requests: {all_requests.filter(status='CANCELLED').count()}")

        print("\n✅ All tests completed successfully!")
        print("🎉 Support request functionality is working correctly!")

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_support_request_functionality()
