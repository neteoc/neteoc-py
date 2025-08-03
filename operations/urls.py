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
    path(
        "incident/<int:incident_id>/request-support/",
        views.request_support_for_incident,
        name="request_support_for_incident",
    ),
    # Organization management URLs
    path("organizations/", views.organization_list, name="organization_list"),
    path("organizations/<int:org_id>/", views.organization_detail, name="organization_detail"),
    path("organizations/<int:org_id>/invite/", views.invite_user, name="invite_user"),
    path(
        "organizations/<int:org_id>/manage-role/<int:user_id>/",
        views.manage_user_role,
        name="manage_user_role",
    ),
    # Organization public profile and support request URLs
    path(
        "organizations/<int:org_id>/profile/",
        views.organization_public_profile,
        name="organization_public_profile",
    ),
    path(
        "organizations/<int:org_id>/request-support/", views.request_support, name="request_support"
    ),
    path("support/requests/", views.support_requests_list, name="support_requests_list"),
    path(
        "support/requests/<int:request_id>/",
        views.support_request_detail,
        name="support_request_detail",
    ),
    # Organization switching URLs
    path(
        "switch-organization/<int:org_id>/", views.switch_organization, name="switch_organization"
    ),
    path("clear-organization/", views.clear_organization, name="clear_organization"),
    # Asset management URLs
    path("assets/", views.asset_list, name="asset_list"),
    path("assets/<int:asset_id>/", views.asset_detail, name="asset_detail"),
    path("assets/create/", views.asset_create, name="asset_create"),
    path("assets/<int:asset_id>/edit/", views.asset_edit, name="asset_edit"),
    path("assets/<int:asset_id>/checkout/", views.asset_checkout, name="asset_checkout"),
    path(
        "assets/checkout/<int:checkout_id>/accept/",
        views.asset_accept_checkout,
        name="asset_accept_checkout",
    ),
    path("assets/checkout/<int:checkout_id>/checkin/", views.asset_checkin, name="asset_checkin"),
    path(
        "assets/checkout/<int:checkout_id>/cancel/",
        views.asset_cancel_checkout,
        name="asset_cancel_checkout",
    ),
    path("assets/categories/", views.asset_category_list, name="asset_category_list"),
    path("assets/categories/create/", views.asset_category_create, name="asset_category_create"),
    path("assets/my/", views.my_assets, name="my_assets"),
    # Time Tracking URLs
    path("time/", views.time_entry_list, name="time_entry_list"),
    path("time/new/", views.time_entry_create, name="time_entry_create"),
    path("time/<int:entry_id>/", views.time_entry_detail, name="time_entry_detail"),
    path("time/<int:entry_id>/edit/", views.time_entry_edit, name="time_entry_edit"),
    path("time/<int:entry_id>/delete/", views.time_entry_delete, name="time_entry_delete"),
]
