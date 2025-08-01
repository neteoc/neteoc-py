from django.urls import path
from . import views

app_name = "operations"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("checkin/", views.index, name="checkin_index"),
    path("checkin/new/<int:incident_id>/", views.new, name="checkin_new"),
    path("checkin/report/", views.report.as_view(), name="checkin_report"),
    path("checkin/checkout/<int:pk>/", views.checkout, name="checkin_checkout"),
]
