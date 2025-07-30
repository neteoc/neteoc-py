from django.urls import path
from django.contrib.auth.decorators import login_required


from . import views

app_name = "checkin"

urlpatterns = [
    path("new/", views.new, name="new"),
    path(
        "report/",
        login_required(views.report.as_view(), login_url="/admin/login/"),
        name="report",
    ),
    path(
        "checkout/<int:pk>/",
        login_required(views.checkout, login_url="/admin/login/"),
        name="checkout",
    ),
    path("", views.index, name="index"),
]
