from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, viewsets
from rest_framework.decorators import action

from .forms import UserProfileForm, PublicUserProfileForm, ContactForm, ContactDeleteForm
from .models import UserProfile, Contact
from .serializers import UserRosterSerializer, ContactSerializer, ContactListSerializer

# Import organization models for displaying user memberships
try:
    from operations.models import IncidentOrganizationUser
except ImportError:
    IncidentOrganizationUser = None

from logging import getLogger

logger = getLogger(__name__)

# URL constants
PROFILE_URL = "user_profile:profile"


@login_required()
def profile(request):
    """
    Allow users to manage their profile including roster ID and address
    """
    # Get or create the user's profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Handle two forms: profile and public profile
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "profile":
            form = UserProfileForm(request.POST, instance=user_profile)
            public_profile_form = PublicUserProfileForm(instance=user_profile)
            if form.is_valid():
                form.save(request.user)
                messages.success(request, "Your profile has been updated successfully!")
                return redirect(PROFILE_URL)
            else:
                messages.error(request, "Please correct the errors below.")
        elif form_type == "public_profile":
            form = UserProfileForm(instance=user_profile)
            public_profile_form = PublicUserProfileForm(request.POST, instance=user_profile)
            if public_profile_form.is_valid():
                public_profile_form.save()
                messages.success(request, "Your public profile has been updated!")
                return redirect(PROFILE_URL)
            else:
                messages.error(request, "Please correct the errors below in your public profile.")
        else:
            form = UserProfileForm(instance=user_profile)
            public_profile_form = PublicUserProfileForm(instance=user_profile)
    else:
        form = UserProfileForm(instance=user_profile)
        public_profile_form = PublicUserProfileForm(instance=user_profile)

    # Get user's organization memberships
    user_organizations = []
    if IncidentOrganizationUser:
        user_organizations = (
            IncidentOrganizationUser.objects.filter(user=request.user)
            .select_related("organization")
            .order_by("organization__name")
        )

    context = {
        "form": form,
        "public_profile_form": public_profile_form,
        "user_profile": user_profile,
        "created": created,
        "user_organizations": user_organizations,
    }

    return render(request, "user_profile/profile.html", context)


class UserRosterAPIView(APIView):
    """
    API endpoint to get a user's roster ID and names for auto-population in check-in forms
    Requires authentication to protect user data

    Security Features:
    - Requires user authentication
    - Rate limiting applied via DRF settings
    - Read-only access to user data
    - Serialized data output for consistency
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """
        Get user roster information by user ID

        Args:
            request: The HTTP request object
            user_id: The ID of the user to retrieve information for

        Returns:
            Response: JSON response with user roster data or error message

        Security Notes:
            - Only authenticated users can access this endpoint
            - Returns limited user information (no sensitive data)
            - Logs access attempts for security auditing
        """
        logger.info(f"User {request.user.username} requested roster data for user ID {user_id}")

        try:
            user = User.objects.get(id=user_id)
            serializer = UserRosterSerializer(user)

            logger.info(f"Successfully retrieved roster data for user {user.username}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.warning(f"User {request.user.username} requested non-existent user ID {user_id}")
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in UserRosterAPIView: {str(e)}")
            return Response(
                {"error": "An error occurred while retrieving user data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@login_required()
def edit_public_profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = PublicUserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your public profile has been updated!")
            return redirect(PROFILE_URL)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PublicUserProfileForm(instance=user_profile)
    return render(
        request,
        "user_profile/public_profile_edit.html",
        {"form": form, "user_profile": user_profile},
    )


@login_required()
def view_public_profile(request, user_id):
    # Get target user and profile
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404("User not found")
    target_profile, _ = UserProfile.objects.get_or_create(user=target_user)

    # Access control: must share org or be checked in to incident where target is commander
    # OR be viewing your own profile
    allowed = False

    # Allow users to view their own public profile
    if request.user == target_user:
        allowed = True
    else:
        if IncidentOrganizationUser:
            # Shared org
            my_orgs = IncidentOrganizationUser.objects.filter(user=request.user).values_list(
                "organization", flat=True
            )
            target_orgs = IncidentOrganizationUser.objects.filter(user=target_user).values_list(
                "organization", flat=True
            )
            if set(my_orgs) & set(target_orgs):
                allowed = True
        # Incident commander check
        try:
            from operations.models import CheckIn

            is_checked_in = CheckIn.objects.filter(
                user=request.user, incident__incident_commander=target_user, Check_Out=False
            ).exists()
            if is_checked_in:
                allowed = True
        except Exception:
            pass

    # For other users, also check if the profile is set to be publicly visible
    if not allowed or (request.user != target_user and not target_profile.public_visible):
        raise Http404("Not authorized to view this public profile.")
    return render(
        request,
        "user_profile/public_profile_view.html",
        {"target_user": target_user, "target_profile": target_profile},
    )


# Contact Management Views


@login_required
def contact_list(request):
    """
    Display user's contacts with filtering by organization
    """
    # Get organization filter
    org_filter = request.GET.get("organization", "all")

    # Get user's contacts
    if org_filter == "all":
        contacts = Contact.objects.filter(user=request.user, is_active=True).select_related(
            "organization"
        )
    elif org_filter == "global":
        contacts = Contact.objects.filter(
            user=request.user, organization__isnull=True, is_active=True
        )
    else:
        try:
            org_id = int(org_filter)
            contacts = Contact.objects.filter(
                user=request.user, organization_id=org_id, is_active=True
            ).select_related("organization")
        except (ValueError, TypeError):
            contacts = Contact.objects.filter(user=request.user, is_active=True).select_related(
                "organization"
            )

    contacts = contacts.order_by("contact_type", "-is_primary", "value")

    # Get user's organizations for filter dropdown
    user_organizations = []
    if IncidentOrganizationUser:
        user_organizations = (
            IncidentOrganizationUser.objects.filter(user=request.user)
            .select_related("organization")
            .order_by("organization__name")
        )

    context = {
        "contacts": contacts,
        "user_organizations": user_organizations,
        "org_filter": org_filter,
    }

    return render(request, "user_profile/contacts.html", context)


@login_required
def contact_create(request):
    """
    Create a new contact
    """
    if request.method == "POST":
        form = ContactForm(request.POST, user=request.user)
        if form.is_valid():
            contact = form.save()
            messages.success(request, f"Contact {contact.value} created successfully!")
            return redirect("user_profile:contact_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm(user=request.user)

    context = {
        "form": form,
        "action": "Create",
    }

    return render(request, "user_profile/contact_form.html", context)


@login_required
def contact_edit(request, contact_id):
    """
    Edit an existing contact
    """
    contact = get_object_or_404(Contact, id=contact_id, user=request.user, is_active=True)

    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact, user=request.user)
        if form.is_valid():
            updated_contact = form.save()
            messages.success(request, f"Contact {updated_contact.value} updated successfully!")
            return redirect("user_profile:contact_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm(instance=contact, user=request.user)

    context = {
        "form": form,
        "contact": contact,
        "action": "Edit",
    }

    return render(request, "user_profile/contact_form.html", context)


@login_required
def contact_delete(request, contact_id):
    """
    Soft delete a contact (confirmation required)
    """
    contact = get_object_or_404(Contact, id=contact_id, user=request.user, is_active=True)

    if request.method == "POST":
        form = ContactDeleteForm(request.POST)
        if form.is_valid():
            # Soft delete the contact
            contact.is_active = False
            contact.save()
            messages.success(request, f"Contact {contact.value} deleted successfully!")
            return redirect("user_profile:contact_list")
        else:
            messages.error(request, "Please confirm the deletion.")
    else:
        form = ContactDeleteForm()

    context = {
        "form": form,
        "contact": contact,
    }

    return render(request, "user_profile/contact_delete.html", context)


@login_required
def contact_detail(request, contact_id):
    """
    Display contact details (JSON response for AJAX)
    """
    contact = get_object_or_404(Contact, id=contact_id, user=request.user, is_active=True)

    data = {
        "id": contact.id,
        "contact_type": contact.get_contact_type_display(),
        "value": contact.value,
        "organization": contact.organization.name if contact.organization else "Global",
        "is_primary": contact.is_primary,
        "created_at": contact.created_at.strftime("%Y-%m-%d %H:%M"),
        "updated_at": contact.updated_at.strftime("%Y-%m-%d %H:%M"),
    }

    return JsonResponse(data)


# Contact API Views


class ContactViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Contact management

    Provides full CRUD operations for user contacts with proper authentication,
    authorization, and organization context filtering.

    Features:
    - User can only manage their own contacts
    - Organization-based filtering
    - Contact type filtering (email/phone)
    - Primary contact management
    - Soft delete (deactivate instead of delete)
    """

    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter contacts to only show the authenticated user's active contacts
        """
        queryset = Contact.objects.filter(user=self.request.user, is_active=True).select_related(
            "organization"
        )

        # Organization filtering
        org_id = self.request.query_params.get("organization", None)
        if org_id is not None:
            if org_id == "null" or org_id == "":
                queryset = queryset.filter(organization__isnull=True)
            else:
                try:
                    org_id = int(org_id)
                    queryset = queryset.filter(organization_id=org_id)
                except (ValueError, TypeError):
                    pass

        # Contact type filtering
        contact_type = self.request.query_params.get("contact_type", None)
        if contact_type and contact_type in ["EMAIL", "PHONE"]:
            queryset = queryset.filter(contact_type=contact_type)

        return queryset.order_by("contact_type", "-is_primary", "value")

    def get_serializer_class(self):
        """
        Use different serializers for list vs detail views
        """
        if self.action == "list":
            return ContactListSerializer
        return ContactSerializer

    def get_serializer_context(self):
        """
        Add user to serializer context for validation
        """
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def perform_create(self, serializer):
        """
        Set the user when creating a contact
        """
        # Handle primary contact logic
        contact_data = serializer.validated_data
        if contact_data.get("is_primary"):
            # Unset other primary contacts of same type in same organization context
            Contact.objects.filter(
                user=self.request.user,
                organization=contact_data.get("organization"),
                contact_type=contact_data["contact_type"],
                is_primary=True,
                is_active=True,
            ).update(is_primary=False)

        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Handle primary contact logic during updates
        """
        contact_data = serializer.validated_data
        if contact_data.get("is_primary"):
            # Unset other primary contacts of same type in same organization context
            Contact.objects.filter(
                user=self.request.user,
                organization=contact_data.get("organization"),
                contact_type=contact_data["contact_type"],
                is_primary=True,
                is_active=True,
            ).exclude(pk=self.get_object().pk).update(is_primary=False)

        serializer.save()

    def perform_destroy(self, instance):
        """
        Soft delete: deactivate contact instead of deleting
        """
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=["post"])
    def set_primary(self, request, pk=None):
        """
        Set a contact as primary for its type and organization context

        POST /api/contacts/{id}/set_primary/
        """
        contact = self.get_object()

        # Unset other primary contacts of same type in same organization context
        Contact.objects.filter(
            user=request.user,
            organization=contact.organization,
            contact_type=contact.contact_type,
            is_primary=True,
            is_active=True,
        ).update(is_primary=False)

        # Set this contact as primary
        contact.is_primary = True
        contact.save()

        serializer = self.get_serializer(contact)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def primary(self, request):
        """
        Get primary contacts for the user

        GET /api/contacts/primary/?contact_type=EMAIL&organization=1
        """
        queryset = self.get_queryset().filter(is_primary=True)

        # Apply same filtering as main queryset
        contact_type = request.query_params.get("contact_type", None)
        if contact_type and contact_type in ["EMAIL", "PHONE"]:
            queryset = queryset.filter(contact_type=contact_type)

        serializer = ContactListSerializer(queryset, many=True)
        return Response(serializer.data)
