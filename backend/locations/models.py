from django.db import models

class PlaceCoordinate(models.Model):
    address = models.CharField(max_length=255, unique=True, db_index=True, verbose_name="Адрес")
    lat = models.FloatField(verbose_name="Широта", null=True, blank=True)
    lon = models.FloatField(verbose_name="Долгота", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.address} ({self.lat}, {self.lon})"
