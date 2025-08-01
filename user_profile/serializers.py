from rest_framework import serializers
from django.contrib.auth.models import User


class UserRosterSerializer(serializers.ModelSerializer):
    """
    Serializer for user roster information used in check-in auto-population

    This serializer provides safe access to user information needed for
    check-in operations while protecting sensitive user data.

    Fields:
        - id: User's unique identifier
        - first_name: User's first name
        - last_name: User's last name
        - roster_id: User's roster ID from their profile (if available)

    Security Notes:
        - Only returns public/semi-public user information
        - No sensitive data like email, phone, address included
        - Roster ID access controlled by profile relationship
    """

    roster_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "roster_id"]
        read_only_fields = ["id", "first_name", "last_name", "roster_id"]

    def get_roster_id(self, obj):
        """
        Safely retrieve roster ID from user's profile

        Args:
            obj: User instance

        Returns:
            str: User's roster ID or empty string if not available
        """
        try:
            if hasattr(obj, "profile") and obj.profile:
                return obj.profile.roster_id or ""
            return ""
        except Exception:
            # Return empty string if any error occurs accessing profile
            return ""
