from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserProfile, Address


class UserRosterAPITest(APITestCase):
    """
    Test cases for the User Roster API endpoint
    """

    def setUp(self):
        """Set up test data"""
        # Create test users with secure passwords
        from django.contrib.auth.hashers import make_password
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password=make_password("test_password_123!"),
            first_name="John",
            last_name="Doe",
        )

        self.user_no_profile = User.objects.create_user(
            username="testuser2",
            email="test2@example.com", 
            password=make_password("test_password_456!"),
            first_name="Jane",
            last_name="Smith",
        )

        # Create a test address
        self.address = Address.objects.create(
            street_1="123 Test St", city="Testville", state="TS", zip_code="12345"
        )

        # Create a test user profile for first user only
        # The signal already creates a profile, so we need to update it
        self.user_profile = UserProfile.objects.get(user=self.user)
        self.user_profile.roster_id = "DOE1234"
        self.user_profile.address = self.address
        self.user_profile.save()

    def test_api_requires_authentication(self):
        """Test that API endpoint requires authentication"""
        url = reverse("api:v1:user_profile_api:user_roster", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_user_roster_with_profile(self):
        """Test retrieving user roster data when user has profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse("api:v1:user_profile_api:user_roster", kwargs={"user_id": self.user.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["first_name"], "John")
        self.assertEqual(response.data["last_name"], "Doe")
        self.assertEqual(response.data["roster_id"], "DOE1234")

    def test_get_user_roster_without_profile(self):
        """Test retrieving user roster data when user has no profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "api:v1:user_profile_api:user_roster", kwargs={"user_id": self.user_no_profile.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user_no_profile.id)
        self.assertEqual(response.data["first_name"], "Jane")
        self.assertEqual(response.data["last_name"], "Smith")
        self.assertEqual(response.data["roster_id"], "")  # Empty string for no profile

    def test_get_nonexistent_user(self):
        """Test requesting data for non-existent user"""
        self.client.force_authenticate(user=self.user)
        url = reverse("api:v1:user_profile_api:user_roster", kwargs={"user_id": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "User not found")

    def test_api_root_endpoints(self):
        """Test that API root endpoints work"""
        self.client.force_authenticate(user=self.user)

        # Test main API root
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Test v1 API root
        response = self.client.get("/api/v1/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("version", response.data)
