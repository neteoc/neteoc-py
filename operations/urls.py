from django.urls import path
from . import views

app_name = "operations"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("checkin/", views.index, name="checkin_index"),
    path("checkin/new/<int:incident_id>/", views.new, name="checkin_new"),
    path("checkin/report/", views.report.as_view(), name="checkin_report"),
    path("checkin/checkout/<int:pk>/", views.checkout, name="checkin_checkout"),
    path("incident/create/", views.create_incident, name="incident_create"),
    path("incident/<int:incident_id>/", views.incident_detail, name="incident_detail"),
    # Organization management URLs
    path("organizations/", views.organization_list, name="organization_list"),
    path("organizations/<int:org_id>/", views.organization_detail, name="organization_detail"),
    path("organizations/<int:org_id>/invite/", views.invite_user, name="invite_user"),
    path(
        "organizations/<int:org_id>/manage-role/<int:user_id>/",
        views.manage_user_role,
        name="manage_user_role",
    ),
]
