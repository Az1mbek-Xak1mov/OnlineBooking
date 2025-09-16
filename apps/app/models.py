from django.core.exceptions import ValidationError
from django.db.models import (CASCADE, SET_NULL, CharField,
                              ForeignKey, PositiveIntegerField, TimeField, Model, IntegerField, Index)
from apps.shared.models import UUIDBaseModel, CreatedBaseModel

WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class ServiceCategory(UUIDBaseModel, CreatedBaseModel):
    name = CharField(max_length=255)

    class Meta:
        verbose_name = 'ServiceCategory'
        verbose_name_plural = 'ServiceCategories'

    def __str__(self):
        return self.name


class Service(UUIDBaseModel, CreatedBaseModel):
    owner = ForeignKey('authentication.User', on_delete=CASCADE,
                       limit_choices_to={'type': 'provider'}, related_name="services")
    category = ForeignKey('app.ServiceCategory', on_delete=SET_NULL, null=True, related_name="services")
    name = CharField(max_length=255)
    address = CharField(max_length=255)
    capacity = PositiveIntegerField(default=1)
    # LOCATION

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'


class ServiceSchedule(UUIDBaseModel, CreatedBaseModel):
    service = ForeignKey(Service, on_delete=CASCADE, related_name="schedules")
    weekday = IntegerField(choices=WEEKDAY_CHOICES)
    start_time = TimeField()
    end_time = TimeField()

    class Meta:
        ordering = ("weekday", "start_time")
        indexes = [
            Index(fields=["service", "weekday"]),
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("start_time must be before end_time")


class Booking(UUIDBaseModel, CreatedBaseModel):
    service = ForeignKey(Service, on_delete=CASCADE, related_name="bookings")
    user = ForeignKey('authentication.User', on_delete=CASCADE, related_name="bookings")
    weekday = IntegerField(choices=WEEKDAY_CHOICES)
    start_time = TimeField()
    seats = PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            Index(fields=["service", "weekday", "start_time"]),
        ]
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"{self.user} -> {self.service.name} {self.weekday} {self.start_time} ({self.seats})"

    def clean(self):
        if self.seats > self.service.capacity:
            raise ValidationError("seats can't exceed service capacity")


# Hello world