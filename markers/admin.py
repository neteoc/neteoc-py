from django.contrib.gis import admin
from markers.models import Marker

@admin.register(Marker)
class MarkerAdmin(admin.GISModelAdmin):
    list_display = ("name", "address")
    search_fields = ("name", "address")


