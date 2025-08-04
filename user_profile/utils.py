"""
User profile utility functions for contact management and photo URLs
"""

import hashlib
import urllib.parse
from .models import Contact


def get_user_contacts(user, organization=None, contact_type="all"):
    """
    Retrieve contacts for user in specific organizational context

    Args:
        user: User instance
        organization: IncidentOrganization instance or None for global
        contact_type: 'all', 'EMAIL', or 'PHONE'

    Returns:
        QuerySet of Contact instances
    """
    queryset = Contact.objects.filter(user=user, is_active=True)

    # Filter by organization context
    if organization:
        queryset = queryset.filter(organization=organization)
    else:
        queryset = queryset.filter(organization__isnull=True)

    # Filter by contact type
    if contact_type != "all":
        queryset = queryset.filter(contact_type=contact_type)

    return queryset.select_related("organization").order_by("contact_type", "-is_primary", "value")


def create_user_contact(user, contact_type, value, organization=None, is_primary=False):
    """
    Create new contact with validation and constraint checking

    Args:
        user: User instance
        contact_type: 'EMAIL' or 'PHONE'
        value: Contact value (email address or phone number)
        organization: IncidentOrganization instance or None
        is_primary: Boolean, set as primary contact for this type

    Returns:
        Contact instance

    Raises:
        ValidationError: If contact validation fails
        ValueError: If trying to create duplicate contact
    """
    from django.db import IntegrityError

    # Check for existing contact
    existing = Contact.objects.filter(
        user=user, organization=organization, contact_type=contact_type, value=value, is_active=True
    ).first()

    if existing:
        raise ValueError(f"Contact {value} already exists for this user and organization context")

    # If setting as primary, unset other primary contacts of same type
    if is_primary:
        Contact.objects.filter(
            user=user,
            organization=organization,
            contact_type=contact_type,
            is_primary=True,
            is_active=True,
        ).update(is_primary=False)

    try:
        contact = Contact.objects.create(
            user=user,
            organization=organization,
            contact_type=contact_type,
            value=value,
            is_primary=is_primary,
        )
        return contact
    except IntegrityError as e:
        raise ValueError(f"Failed to create contact: {str(e)}")


def get_primary_contact(user, contact_type, organization=None):
    """
    Get primary contact for user/org/type combination

    Args:
        user: User instance
        contact_type: 'EMAIL' or 'PHONE'
        organization: IncidentOrganization instance or None

    Returns:
        Contact instance or None
    """
    return (
        Contact.objects.filter(
            user=user,
            organization=organization,
            contact_type=contact_type,
            is_primary=True,
            is_active=True,
        )
        .select_related("organization")
        .first()
    )


def get_profile_photo_url(user, size=150, fallback_to_gravatar=True):
    """
    Enhanced photo URL generation with upload support
    Priority: Gravatar (if enabled) -> Bootstrap icon fallback

    Args:
        user: User instance
        size: Image size in pixels (75, 150, 300, 500)
        fallback_to_gravatar: Whether to try Gravatar before fallback icon

    Returns:
        String URL for profile photo
    """
    profile = getattr(user, "profile", None)
    if not profile:
        return get_bootstrap_icon_url()

    # Check if Gravatar is enabled and try to get Gravatar URL
    if fallback_to_gravatar and profile.use_gravatar:
        gravatar_email = profile.gravatar_email or user.email
        if gravatar_email:
            gravatar_url = generate_gravatar_url(gravatar_email, size)
            if gravatar_url:
                return gravatar_url

    # Final fallback to Bootstrap icon
    return get_bootstrap_icon_url()


def generate_gravatar_url(email, size=150, default="mp", force_default=False):
    """
    Generate secure Gravatar URL with proper fallbacks

    Args:
        email: Email address for Gravatar lookup
        size: Image size in pixels (1-2048)
        default: Default behavior ('mp', 'identicon', 'monsterid', 'wavatar', 'retro', 'robohash', 'blank')
        force_default: Force default even if Gravatar exists

    Returns:
        String URL for Gravatar image or None if no email
    """
    if not email:
        return None

    # Normalize email for Gravatar hash (MD5 required by Gravatar spec)
    email_hash = hashlib.md5(
        email.lower().strip().encode("utf-8"), usedforsecurity=False
    ).hexdigest()  # nosec

    # Build query parameters
    params = {
        "s": str(size),  # Size
        "d": default,  # Default behavior
        "r": "pg",  # Rating (family-friendly)
    }

    if force_default:
        params["f"] = "y"  # Force default

    query_string = urllib.parse.urlencode(params)
    return f"https://www.gravatar.com/avatar/{email_hash}?{query_string}"


def get_bootstrap_icon_url():
    """
    Generate Bootstrap icon URL for default avatar

    Returns:
        String URL for Bootstrap person-circle icon
    """
    return "/static/icons/person-circle.svg"


def get_size_pixels(size_name):
    """
    Convert size name to pixel dimensions

    Args:
        size_name: 'small', 'medium', 'large', 'xlarge'

    Returns:
        Integer pixel size
    """
    size_map = {
        "small": 75,
        "medium": 150,
        "large": 300,
        "xlarge": 500,
    }
    return size_map.get(size_name, 150)
