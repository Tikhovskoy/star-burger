from django.contrib import admin
from .models import PlaceCoordinate

@admin.register(PlaceCoordinate)
class PlaceCoordinateAdmin(admin.ModelAdmin):
    list_display = ['address', 'lat', 'lon', 'updated_at']
    search_fields = ['address']
