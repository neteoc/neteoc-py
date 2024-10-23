from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from geopy.geocoders import Nominatim
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Marker(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    location = models.PointField(geography=True, blank=True, null=True)
    description = models.TextField(default="",)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.address:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT ST_X(geomout), ST_Y(geomout) FROM geocode(%s, 1) AS g;",
                    [self.address]
                )
                result = cursor.fetchone()
                if result:
                    longitude, latitude = result
                    self.location = Point(longitude, latitude)
                    logger.info(f"Geocoded {self.address} to (lat: {latitude}, lon: {longitude})")
                else:
                    logger.warning(f"Address {self.address} not found in TIGER/Line geocoding database.")
                    logger.warning(result)
        super().save(*args, **kwargs)
