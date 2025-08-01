"""
URL configuration for neteoc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path
from django.conf import settings
from django.views.generic import RedirectView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls


urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("operations/", include("operations.urls")),
    path("profile/", include("user_profile.urls")),
    # Backward compatibility redirects for old checkin URLs
    path("checkin/", RedirectView.as_view(url="/operations/checkin/", permanent=True)),
    path("checkin/new/", RedirectView.as_view(url="/operations/checkin/new/", permanent=True)),
    path(
        "checkin/report/", RedirectView.as_view(url="/operations/checkin/report/", permanent=True)
    ),
    path("checkin/profile/", RedirectView.as_view(url="/profile/", permanent=True)),
    path(
        "checkin/checkout/<int:pk>/",
        RedirectView.as_view(url="/operations/checkin/checkout/%(pk)s/", permanent=True),
    ),
    path(
        "checkin/get_user_roster_id/<int:user_id>/",
        RedirectView.as_view(url="/profile/api/user/%(user_id)s/roster/", permanent=True),
    ),
    path("admin/", admin.site.urls),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("", include(wagtail_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
