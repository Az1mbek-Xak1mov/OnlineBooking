from authentication.forms import LocationModelForm
from django.contrib import admin

from .models import Location, Service, ServiceSchedule


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = "name", "lat", "lng"
    form = LocationModelForm

    fieldsets = (
        (None, {
            "fields": ("name", "lat", "lng")
        }),
        ("Location Map", {
            "fields": ("location_map",),
        }),
    )


@admin.register(ServiceSchedule)
class ServiceScheduleAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'duration']
