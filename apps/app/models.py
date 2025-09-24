from datetime import date as date_cls
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db.models import (CASCADE, SET_NULL, CharField,
                              DurationField, FloatField, ForeignKey, Index,
                              IntegerField, Model, PositiveIntegerField,
                              TextChoices, TextField, TimeField)
from django.db.models.fields import DateField
from django.utils import timezone

from apps.shared.models import CreatedBaseModel, UUIDBaseModel

WEEKDAY_NAME_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class WeekdayChoices(TextChoices):
    MONDAY = 'monday', 'Monday'
    TUESDAY = 'tuesday', 'Tuesday'
    WEDNESDAY = 'wednesday', 'Wednesday'
    THURSDAY = 'thursday', 'Thursday'
    FRIDAY = 'friday', 'Friday'
    SATURDAY = 'saturday', 'Saturday'
    SUNDAY = 'sunday', 'Sunday'


class Park(Model):
    name = CharField(max_length=100)
    lat = FloatField()
    lng = FloatField()
    size = IntegerField(help_text="Size in acres")

    def __str__(self):
        return self.name


class ServiceCategory(UUIDBaseModel, CreatedBaseModel):
    name = CharField(max_length=255)

    class Meta:
        verbose_name = 'ServiceCategory'
        verbose_name_plural = 'ServiceCategories'

    def __str__(self):
        return self.name


class Service(UUIDBaseModel, CreatedBaseModel):
    owner = ForeignKey('authentication.User', CASCADE,
                       limit_choices_to={'type': 'provider'}, related_name="services")
    category = ForeignKey('app.ServiceCategory', SET_NULL, null=True, related_name="services")
    name = CharField(max_length=255)
    address = CharField(max_length=255)
    capacity = PositiveIntegerField(default=1)
    duration = DurationField(default=timedelta(minutes=60))  # TODO validator qoshish kk 60 ga karralimi? + pg check
    price = PositiveIntegerField()
    description = TextField(blank=True)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

        # constraints = [
        #     CheckConstraint(name='rating_check_constraints')
        # ]


class ServiceSchedule(UUIDBaseModel, CreatedBaseModel):
    service = ForeignKey('app.Service', CASCADE, related_name="schedules")
    weekday = CharField(max_length=9, choices=WeekdayChoices.choices)
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

    @property
    def start_time_hm(self):
        return self.start_time.strftime("%H:%M") if self.start_time else None


class Booking(UUIDBaseModel, CreatedBaseModel):
    service = ForeignKey("app.Service", on_delete=CASCADE, related_name="bookings")
    weekday = CharField(max_length=9, choices=WeekdayChoices.choices)
    user = ForeignKey('authentication.User', CASCADE, related_name="bookings")
    date = DateField()
    start_time = TimeField()
    end_time = TimeField()
    seats = PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            Index(fields=["service", "weekday", "start_time", "end_time"]),
        ]
        ordering = '-created_at',
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"{self.user} -> {self.service.name} {self.weekday} {self.start_time} {self.end_time} ({self.seats})"

    def clean(self):
        if self.seats > self.service.capacity:
            raise ValidationError("seats can't exceed service capacity")

    @property
    def start_time_hm(self):
        return self.start_time.strftime("%H:%M") if self.start_time else None

    def save(self, *args, **kwargs):
        if self.start_time:
            start = self.start_time.replace(second=0, microsecond=0)
        else:
            start = None
        if not self.date and self.weekday:
            name = str(self.weekday).lower()
            if name not in WEEKDAY_NAME_TO_INDEX:
                raise ValueError(f"Unknown weekday value: {self.weekday}")
            target_idx = WEEKDAY_NAME_TO_INDEX[name]
            today = timezone.localdate()
            today_idx = today.weekday()
            delta_days = (target_idx - today_idx) % 7
            candidate_date = today + timedelta(days=delta_days)

            if delta_days == 0 and start is not None:
                now_time = timezone.localtime().time()
                if start <= now_time:
                    candidate_date = candidate_date + timedelta(days=7)

            self.date = candidate_date

        if start:
            dt_start = datetime.combine(date_cls.min, start)
            dt_end = dt_start + timedelta(hours=1)
            self.end_time = dt_end.time().replace(second=0, microsecond=0)

        super().save(*args, **kwargs)
