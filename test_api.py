#!/usr/bin/env python
"""
Quick test script to verify the Contact API endpoints
"""

import os
import django
import json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neteoc.settings")
django.setup()

# Django imports must come after setup() call for standalone scripts
# ruff: noqa: E402
from django.contrib.auth.models import User
from django.test import Client
from user_profile.models import Contact


def test_contact_api():
    """Test the Contact API endpoints"""

    # Get the first user
    user = User.objects.get(id=1)
    print(f"Testing Contact API for user: {user.username} (ID: {user.id})")

    # Create a test client and force authentication
    client = Client()
    client.force_login(user)

    # Clean up any existing test contacts
    Contact.objects.filter(user=user, value__startswith="test-api-").delete()

    print("\n1. Testing Contact Creation...")
    # Test creating a contact
    create_data = {
        "contact_type": "EMAIL",
        "value": "test-api-contact@example.com",
        "is_primary": True,
        "organization": None,
    }

    response = client.post(
        "/api/v1/user-profile/contacts/",
        data=json.dumps(create_data),
        content_type="application/json",
    )

    print(f"Create Status Code: {response.status_code}")
    if response.status_code == 201:
        created_contact = response.json()
        contact_id = created_contact["id"]
        print("✅ Contact created successfully!")
        print(f"   ID: {created_contact['id']}")
        print(f"   Type: {created_contact['contact_type_display']}")
        print(f"   Value: {created_contact['value']}")
        print(f"   Primary: {created_contact['is_primary']}")
    else:
        print(f"❌ Contact creation failed: {response.content.decode()}")
        return

    print("\n2. Testing Contact List...")
    # Test listing contacts
    response = client.get("/api/v1/user-profile/contacts/")
    print(f"List Status Code: {response.status_code}")
    if response.status_code == 200:
        contacts = response.json()
        print(f"✅ Found {len(contacts)} contacts")
        for contact in contacts:
            print(
                f"   - {contact['contact_type_display']}: {contact['value']} (Primary: {contact['is_primary']})"
            )
    else:
        print(f"❌ Contact list failed: {response.content.decode()}")

    print("\n3. Testing Contact Update...")
    # Test updating the contact
    update_data = {
        "contact_type": "EMAIL",
        "value": "test-api-updated@example.com",
        "is_primary": True,
        "organization": None,
    }

    response = client.put(
        f"/api/v1/user-profile/contacts/{contact_id}/",
        data=json.dumps(update_data),
        content_type="application/json",
    )

    print(f"Update Status Code: {response.status_code}")
    if response.status_code == 200:
        updated_contact = response.json()
        print("✅ Contact updated successfully!")
        print(f"   New Value: {updated_contact['value']}")
    else:
        print(f"❌ Contact update failed: {response.content.decode()}")

    print("\n4. Testing Primary Contact Action...")
    # Test primary contact endpoint
    response = client.get("/api/v1/user-profile/contacts/primary/")
    print(f"Primary Contacts Status Code: {response.status_code}")
    if response.status_code == 200:
        primary_contacts = response.json()
        print(f"✅ Found {len(primary_contacts)} primary contacts")
        for contact in primary_contacts:
            print(f"   - {contact['contact_type_display']}: {contact['value']}")
    else:
        print(f"❌ Primary contacts failed: {response.content.decode()}")

    print("\n5. Testing Contact Deletion...")
    # Test deleting the contact (soft delete)
    response = client.delete(f"/api/v1/user-profile/contacts/{contact_id}/")
    print(f"Delete Status Code: {response.status_code}")
    if response.status_code == 204:
        print("✅ Contact deleted successfully!")

        # Verify it's soft deleted (not in active list)
        response = client.get("/api/v1/user-profile/contacts/")
        if response.status_code == 200:
            active_contacts = response.json()
            deleted_contact_exists = any(c["id"] == contact_id for c in active_contacts)
            if not deleted_contact_exists:
                print("✅ Contact properly soft deleted (not in active list)")
            else:
                print("❌ Contact still appears in active list")
    else:
        print(f"❌ Contact deletion failed: {response.content.decode()}")

    print("\n📋 Contact API Test Summary Complete!")


def test_user_roster_api():
    """Test the User Roster API endpoint"""

    # Get the first user
    user = User.objects.get(id=1)
    print(f"\nTesting User Roster API for user: {user.username} (ID: {user.id})")

    # Create a test client and force authentication
    client = Client()
    client.force_login(user)

    # Test the API endpoint
    url = f"/api/v1/user-profile/user/{user.id}/roster/"
    print(f"Testing URL: {url}")

    response = client.get(url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("✅ User Roster API Test Successful!")
        print(f"   User ID: {data.get('id')}")
        print(f"   First Name: {data.get('first_name')}")
        print(f"   Last Name: {data.get('last_name')}")
        print(f"   Roster ID: {data.get('roster_id')}")
    else:
        print(f"❌ User Roster API Test Failed: {response.content.decode()}")


if __name__ == "__main__":
    print("🧪 Starting API Tests...")
    test_contact_api()
    test_user_roster_api()
    print("\n🎉 All API tests completed!")
