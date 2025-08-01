#!/usr/bin/env python
"""
Quick test script to verify the User Roster API endpoint
"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neteoc.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client


def test_api_endpoint():
    """Test the User Roster API endpoint"""

    # Get the first user
    user = User.objects.get(id=1)
    print(f"Testing API for user: {user.username} (ID: {user.id})")

    # Create a test client and force authentication
    client = Client()
    client.force_login(user)

    # Test the API endpoint
    url = f"/api/v1/user-profile/user/{user.id}/roster/"
    print(f"Testing URL: {url}")

    response = client.get(url)

    print(f"Status Code: {response.status_code}")
    print(f"Response Data: {response.json()}")

    if response.status_code == 200:
        data = response.json()
        print("\n✅ API Test Successful!")
        print(f"   User ID: {data.get('id')}")
        print(f"   Username: {data.get('username')}")
        print(f"   First Name: {data.get('first_name')}")
        print(f"   Last Name: {data.get('last_name')}")
        print(f"   Roster ID: {data.get('roster_id')}")
        print(f"   Email: {data.get('email')}")
    else:
        print(f"❌ API Test Failed: {response.content}")


if __name__ == "__main__":
    test_api_endpoint()
