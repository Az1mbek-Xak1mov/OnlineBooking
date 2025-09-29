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
    list_display = ['id', 'service__name', 'weekday', 'start_time', 'end_time']
    list_select_related = ['service']
    list_filter = ['weekday']
    search_fields = ['service__name']


class ServiceScheduleStackedInline(admin.StackedInline):
    model = ServiceSchedule
    min_num = 0
    extra = 0


@admin.register(Service)
class ServiceModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'duration']
    inlines = (ServiceScheduleStackedInline,)
