from datetime import timedelta

from app.managers import ServiceManager, ServiceQuerySet
from django.core.exceptions import ValidationError
from django.db.models import (CASCADE, SET_NULL, BooleanField, CharField,
                              CheckConstraint, DateField, DurationField,
                              FloatField, ForeignKey, ImageField, Index, Model,
                              PositiveIntegerField, TextChoices, TextField,
                              TimeField, UniqueConstraint, OneToOneField)
from django.db.models.expressions import RawSQL
from django.utils import timezone

from apps.shared.models import CreatedBaseModel, UUIDBaseModel



class WeekdayChoices(TextChoices):
    MONDAY = 'monday', 'Monday'
    TUESDAY = 'tuesday', 'Tuesday'
    WEDNESDAY = 'wednesday', 'Wednesday'
    THURSDAY = 'thursday', 'Thursday'
    FRIDAY = 'friday', 'Friday'
    SATURDAY = 'saturday', 'Saturday'
    SUNDAY = 'sunday', 'Sunday'


class Location(CreatedBaseModel):
    service = OneToOneField('app.Service', CASCADE, related_name="location" )
    name = CharField(max_length=100)
    lat = FloatField()
    lng = FloatField()

    def __str__(self):
        return self.name


class ServiceCategory(CreatedBaseModel):
    name = CharField(max_length=255 , unique=True)
    class Meta:
        verbose_name = 'ServiceCategory'
        verbose_name_plural = 'ServiceCategories'

    def __str__(self):
        return self.name


class Service(CreatedBaseModel):
    owner = ForeignKey('authentication.User', CASCADE,
                       limit_choices_to={'type': 'provider'}, related_name="services")
    category = ForeignKey('app.ServiceCategory', SET_NULL, null=True, related_name="services")
    name = CharField(max_length=255 , unique=True )
    address = CharField(max_length=255)
    capacity = PositiveIntegerField(default=1)
    duration = DurationField(default=timedelta(minutes=60))
    price = PositiveIntegerField()
    description = TextField(blank=True , null=True)
    is_deleted = BooleanField(default=False)

    objects = ServiceManager.from_queryset(ServiceQuerySet)()


    class Meta:
        constraints = [
            CheckConstraint(
                check=RawSQL(
                    "(EXTRACT(EPOCH FROM duration) / 60)::integer %% 30 = 0 AND duration > INTERVAL '0 seconds'",
                    [],
                    output_field=BooleanField()
                ),
                name="duration_multiple_of_30_check"
            )
        ]


class ServiceSchedule(CreatedBaseModel):
    service = ForeignKey('app.Service', CASCADE, related_name="schedules")
    weekday = CharField(max_length=9, choices=WeekdayChoices.choices)
    start_time = TimeField()
    end_time = TimeField()

    class Meta:
        ordering = ("weekday", "start_time")
        indexes = [
            Index(fields=["service", "weekday"]),
        ]

        constraints = [
            UniqueConstraint(fields=['service', 'weekday'], name='unique_service_weekday')
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("start_time must be before end_time")

        if ServiceSchedule.objects.filter(service=self.service, weekday=self.weekday).exclude(pk=self.pk).exists():
            raise ValidationError({'weekday': 'This weekday is already used for this service.'})

    @property
    def start_time_hm(self):
        return self.start_time.strftime("%H:%M") if self.start_time else None


class Booking(CreatedBaseModel):
    service = ForeignKey(
        "app.Service",
        on_delete=CASCADE,
        related_name="bookings"
    )
    weekday = CharField(
        max_length=9,
        choices=WeekdayChoices.choices
    )
    user = ForeignKey(
        'authentication.User',
        CASCADE,
        related_name="bookings"
    )
    date = DateField(blank=True, null=True)
    start_time = TimeField()
    duration = DurationField()
    seats = PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            Index(fields=["service", "weekday", "start_time"]),
        ]
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.user} -> {self.service.name} {self.weekday} {self.start_time} ({self.seats})"

    @property
    def start_time_hm(self):
        return self.start_time.strftime("%H:%M") if self.start_time else None

    def clean(self):
        if self.seats > self.service.capacity:
            raise ValidationError("Seats can't exceed service capacity")

        service_duration = self.service.duration

        if not self.duration:
            self.duration = service_duration
        else:
            if self.duration.total_seconds() % service_duration.total_seconds() != 0:
                raise ValidationError(
                    f"Booking duration must be a multiple of service duration ({service_duration})."
                )

        if self.weekday not in WeekdayChoices.values:
            raise ValidationError(f"Invalid weekday: {self.weekday}")

        if not self.date and self.weekday:
            name = str(self.weekday).lower()
            target_idx = list(WeekdayChoices.values).index(name)
            today = timezone.localdate()
            today_idx = today.weekday()
            delta_days = (target_idx - today_idx) % 7

            candidate_date = today + timedelta(days=delta_days)

            if delta_days == 0 and self.start_time is not None:
                now_time = timezone.localtime().time()
                if self.start_time <= now_time:
                    candidate_date += timedelta(days=7)

            self.date = candidate_date

    def save(self, *args, **kwargs):
        if self.start_time:
            self.start_time = self.start_time.replace(second=0, microsecond=0)

        self.clean()

        super().save(*args, **kwargs)

class Demand(CreatedBaseModel):
    user = ForeignKey(
        'authentication.User',
        CASCADE,
        related_name="demands")
    main_text=TextField(blank=True)