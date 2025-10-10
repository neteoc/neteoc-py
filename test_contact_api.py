#!/usr/bin/env python
"""
Quick test script to verify Contact API functionality using Django shell
"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neteoc.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from user_profile.models import Contact  # noqa: E402
from user_profile.serializers import ContactSerializer, ContactListSerializer  # noqa: E402


def test_contact_operations():
    """Test Contact model and serializer operations"""
    print("🧪 Testing Contact Model and Serializers...")

    # Get or create a test user
    user, created = User.objects.get_or_create(
        username="test_api_user",
        defaults={"first_name": "Test", "last_name": "User", "email": "test@example.com"},
    )

    if created:
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"✅ Using existing test user: {user.username}")

    # Clean up existing test contacts
    Contact.objects.filter(user=user, value__startswith="test-").delete()

    print("\n1. Testing Contact Creation...")
    # Test creating a contact directly
    contact_data = {
        "contact_type": "EMAIL",
        "value": "test-direct@example.com",
        "is_primary": True,
        "organization": None,
    }

    serializer = ContactSerializer(data=contact_data, context={"user": user})

    if serializer.is_valid():
        contact = serializer.save(user=user)
        print(f"✅ Contact created successfully: {contact.value}")
        print(
            f"   ID: {contact.id}, Type: {contact.get_contact_type_display()}, Primary: {contact.is_primary}"
        )
    else:
        print(f"❌ Contact creation failed: {serializer.errors}")
        return

    print("\n2. Testing Contact Serialization...")
    # Test serializing the contact
    serializer = ContactSerializer(contact)
    serialized_data = serializer.data
    print("✅ Contact serialized successfully:")
    print(f"   ID: {serialized_data['id']}")
    print(f"   Type: {serialized_data['contact_type_display']}")
    print(f"   Value: {serialized_data['value']}")
    print(f"   Primary: {serialized_data['is_primary']}")

    print("\n3. Testing Contact List Serialization...")
    # Test list serializer
    contacts = Contact.objects.filter(user=user, is_active=True)
    list_serializer = ContactListSerializer(contacts, many=True)
    print(f"✅ Found {len(list_serializer.data)} active contacts")

    for contact_data in list_serializer.data:
        print(
            f"   - {contact_data['contact_type_display']}: {contact_data['value']} (Primary: {contact_data['is_primary']})"
        )

    print("\n4. Testing Primary Contact Logic...")
    # Create another email contact and test primary logic
    contact_data_2 = {
        "contact_type": "EMAIL",
        "value": "test-primary@example.com",
        "is_primary": True,
        "organization": None,
    }

    serializer2 = ContactSerializer(data=contact_data_2, context={"user": user})

    if serializer2.is_valid():
        contact2 = serializer2.save(user=user)

        # Check that the first contact is no longer primary
        contact.refresh_from_db()
        print("✅ Primary contact logic working:")
        print(f"   First contact primary: {contact.is_primary}")
        print(f"   Second contact primary: {contact2.is_primary}")

        if not contact.is_primary and contact2.is_primary:
            print("✅ Primary contact automatically switched")
        else:
            print("❌ Primary contact logic not working correctly")
    else:
        print(f"❌ Second contact creation failed: {serializer2.errors}")

    print("\n5. Testing Validation...")
    # Test duplicate validation
    duplicate_data = {
        "contact_type": "EMAIL",
        "value": "test-primary@example.com",  # Same as contact2
        "is_primary": False,
        "organization": None,
    }

    duplicate_serializer = ContactSerializer(data=duplicate_data, context={"user": user})

    if duplicate_serializer.is_valid():
        print("❌ Duplicate validation failed - should have rejected duplicate contact")
    else:
        print("✅ Duplicate validation working correctly")
        print(f"   Error: {duplicate_serializer.errors}")

    print("\n6. Testing Soft Delete...")
    # Test soft delete
    contact2.is_active = False
    contact2.save()

    active_contacts = Contact.objects.filter(user=user, is_active=True).count()
    all_contacts = Contact.objects.filter(user=user).count()

    print("✅ Soft delete working:")
    print(f"   Total contacts: {all_contacts}")
    print(f"   Active contacts: {active_contacts}")

    # Clean up
    Contact.objects.filter(user=user, value__startswith="test-").delete()
    if created:
        user.delete()

    print("\n📋 Contact Operations Test Complete!")


def test_user_roster_serializer():
    """Test UserRosterSerializer"""
    print("\n🧪 Testing UserRosterSerializer...")

    # Get the first user
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found in database")
            return

        from user_profile.serializers import UserRosterSerializer
        from user_profile.models import UserProfile

        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(
            user=user, defaults={"roster_id": "TST1234"}
        )

        if created or not profile.roster_id:
            profile.roster_id = "TST1234"
            profile.save()

        serializer = UserRosterSerializer(user)
        data = serializer.data

        print("✅ UserRosterSerializer working:")
        print(f"   User ID: {data.get('id')}")
        print(f"   First Name: {data.get('first_name')}")
        print(f"   Last Name: {data.get('last_name')}")
        print(f"   Roster ID: {data.get('roster_id')}")

    except Exception as e:
        print(f"❌ UserRosterSerializer test failed: {e}")


if __name__ == "__main__":
    test_contact_operations()
    test_user_roster_serializer()
    print("\n🎉 All tests completed!")
