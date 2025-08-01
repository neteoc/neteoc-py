from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .forms import UserProfileForm, PublicUserProfileForm
from .models import UserProfile
from .serializers import UserRosterSerializer

# Import organization models for displaying user memberships
try:
    from operations.models import IncidentOrganizationUser
except ImportError:
    IncidentOrganizationUser = None

from logging import getLogger

logger = getLogger(__name__)


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
                return redirect("user_profile:profile")
            else:
                messages.error(request, "Please correct the errors below.")
        elif form_type == "public_profile":
            form = UserProfileForm(instance=user_profile)
            public_profile_form = PublicUserProfileForm(request.POST, instance=user_profile)
            if public_profile_form.is_valid():
                public_profile_form.save()
                messages.success(request, "Your public profile has been updated!")
                return redirect("user_profile:profile")
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
            return redirect("user_profile:profile")
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
