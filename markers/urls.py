from django.urls import path

from markers.views import MapView

urlpatterns = [
    path("map/", MapView.as_view()),
    
]
