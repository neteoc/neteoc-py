from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Contact


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


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model with organization context

    Provides full CRUD operations for user contacts with proper validation
    and organization relationship handling.
    """

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    contact_type_display = serializers.CharField(source="get_contact_type_display", read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "contact_type",
            "contact_type_display",
            "value",
            "organization",
            "organization_name",
            "is_primary",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "organization_name",
            "contact_type_display",
        ]

    def validate(self, data):
        """
        Validate contact data with organization context
        """
        # Get the user from the context (set by the view)
        user = self.context.get("user")
        if not user:
            raise serializers.ValidationError("User context required for validation")

        contact_type = data.get("contact_type")
        value = data.get("value")
        organization = data.get("organization")

        # Check for duplicate contact (exclude current instance if updating)
        queryset = Contact.objects.filter(
            user=user,
            contact_type=contact_type,
            value=value,
            organization=organization,
            is_active=True,
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                f"A {contact_type.lower()} contact with this value already exists for this organization context."
            )

        return data

    def save(self, **kwargs):
        """
        Handle primary contact logic during save
        """
        # Handle primary contact exclusivity
        if self.validated_data.get("is_primary"):
            user = self.context.get("user") or kwargs.get("user")
            if user:
                # Unset other primary contacts of same type in same organization context
                Contact.objects.filter(
                    user=user,
                    organization=self.validated_data.get("organization"),
                    contact_type=self.validated_data["contact_type"],
                    is_primary=True,
                    is_active=True,
                ).exclude(pk=self.instance.pk if self.instance else None).update(is_primary=False)

        return super().save(**kwargs)

    def validate_value(self, value):
        """
        Validate contact value based on contact type
        """
        contact_type = self.initial_data.get("contact_type")

        if not value or not value.strip():
            raise serializers.ValidationError("Contact value is required.")

        value = value.strip()

        if contact_type == "EMAIL":
            from django.core.validators import EmailValidator

            validator = EmailValidator()
            try:
                validator(value)
            except serializers.ValidationError:
                raise serializers.ValidationError("Enter a valid email address.")

        elif contact_type == "PHONE":
            import re

            if not re.match(r"^[\d\-\(\)\s\+\.]+$", value):
                raise serializers.ValidationError(
                    "Enter a valid phone number (digits, spaces, hyphens, parentheses, and plus signs only)."
                )

        return value


class ContactListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for contact list views

    Optimized for list displays with minimal data transfer
    """

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    contact_type_display = serializers.CharField(source="get_contact_type_display", read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "contact_type",
            "contact_type_display",
            "value",
            "organization_name",
            "is_primary",
            "created_at",
        ]
