from authentication.forms import ParkModelForm
from django.contrib import admin

from .models import Park, Service, ServiceSchedule


@admin.register(Park)
class ParkAdmin(admin.ModelAdmin):
    list_display = "name", "lat", "lng"
    form = ParkModelForm

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
