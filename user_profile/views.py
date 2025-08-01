from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User

from .forms import UserProfileForm
from .models import UserProfile

from logging import getLogger

logger = getLogger(__name__)


@login_required()
def profile(request):
    """
    Allow users to manage their profile including roster ID and address
    """
    # Get or create the user's profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("user_profile:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user_profile)

    context = {"form": form, "user_profile": user_profile, "created": created}

    return render(request, "user_profile/profile.html", context)


@login_required()
def get_user_roster_id(request, user_id):
    """
    AJAX endpoint to get a user's roster ID and names for auto-population
    """
    try:
        user = User.objects.get(id=user_id)
        user_profile = UserProfile.objects.filter(user=user).first()

        data = {
            "roster_id": user_profile.roster_id if user_profile else "",
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
