"""
Template tags for user profile components
"""

from django import template
from ..utils import get_profile_photo_url, get_user_contacts

register = template.Library()


@register.inclusion_tag("components/profile_photo.html")
def profile_photo(user, size="medium", css_class="", alt_text=""):
    """
    Display user profile photo with Gravatar fallback

    Usage:
        {% load profile_tags %}
        {% profile_photo user size="large" css_class="rounded-circle" %}

    Args:
        user: User instance
        size: 'small' (75px), 'medium' (150px), 'large' (300px), 'xlarge' (500px)
        css_class: Additional CSS classes
        alt_text: Alt text for image (defaults to user's name)
    """
    size_pixels = {"small": 75, "medium": 150, "large": 300, "xlarge": 500}.get(size, 150)

    photo_url = get_profile_photo_url(user, size=size_pixels)

    if not alt_text:
        alt_text = f"Profile photo for {user.get_full_name() or user.username}"

    return {
        "photo_url": photo_url,
        "size_pixels": size_pixels,
        "css_class": css_class,
        "alt_text": alt_text,
        "user": user,
    }


@register.inclusion_tag("components/contact_info.html")
def contact_info(user, organization=None, show_phone=True, show_email=True, contact_type="all"):
    """
    Display user contact information

    Usage:
        {% load profile_tags %}
        {% contact_info user organization=current_org show_phone=True %}

    Args:
        user: User instance
        organization: IncidentOrganization instance or None for global
        show_phone: Whether to display phone contacts
        show_email: Whether to display email contacts
        contact_type: 'all', 'EMAIL', or 'PHONE'
    """
    # Filter contact types based on parameters
    if not show_phone and not show_email:
        contacts = []
    elif not show_phone:
        contact_type = "EMAIL"
    elif not show_email:
        contact_type = "PHONE"

    contacts = get_user_contacts(user, organization=organization, contact_type=contact_type)

    return {
        "contacts": contacts,
        "user": user,
        "organization": organization,
        "show_phone": show_phone,
        "show_email": show_email,
    }


@register.simple_tag
def profile_photo_url(user, size="medium"):
    """
    Get profile photo URL as a simple tag

    Usage:
        {% load profile_tags %}
        <img src="{% profile_photo_url user 'large' %}" alt="Profile">
    """
    size_pixels = {"small": 75, "medium": 150, "large": 300, "xlarge": 500}.get(size, 150)

    return get_profile_photo_url(user, size=size_pixels)


@register.filter
def contact_type_icon(contact_type):
    """
    Return Bootstrap icon class for contact type

    Usage:
        {% load profile_tags %}
        <i class="bi {{ contact.contact_type|contact_type_icon }}"></i>
    """
    icons = {
        "EMAIL": "bi-envelope",
        "PHONE": "bi-telephone",
    }
    return icons.get(contact_type, "bi-info-circle")


@register.filter
def contact_type_color(contact_type):
    """
    Return Bootstrap color class for contact type

    Usage:
        {% load profile_tags %}
        <span class="badge bg-{{ contact.contact_type|contact_type_color }}">
    """
    colors = {
        "EMAIL": "primary",
        "PHONE": "success",
    }
    return colors.get(contact_type, "secondary")
