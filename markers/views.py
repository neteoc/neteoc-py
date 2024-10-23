import json

from django.core.serializers import serialize
from django.views.generic import ListView

from markers.models import Marker


class MapView(ListView):
    context_object_name = "markers"
    model = Marker
    template_name = "map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["markers"] = json.loads(
            serialize("geojson", context["markers"])
        )
        return context