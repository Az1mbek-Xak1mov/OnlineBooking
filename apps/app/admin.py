from django.contrib import admin
from django.db.models import Case, When
from django.db.models.fields import IntegerField

from authentication.forms import LocationModelForm
from .models import Location, Service, ServiceSchedule, WeekdayChoices


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
    ordering = (
        Case(
            When(weekday=WeekdayChoices.MONDAY, then=0),
            When(weekday=WeekdayChoices.TUESDAY, then=1),
            When(weekday=WeekdayChoices.WEDNESDAY, then=2),
            When(weekday=WeekdayChoices.THURSDAY, then=3),
            When(weekday=WeekdayChoices.FRIDAY, then=4),
            When(weekday=WeekdayChoices.SATURDAY, then=5),
            When(weekday=WeekdayChoices.SUNDAY, then=6),
            output_field=IntegerField(),
        ),
    )
    min_num = 0
    extra = 0


@admin.register(Service)
class ServiceModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'duration']
    inlines = (ServiceScheduleStackedInline,)
