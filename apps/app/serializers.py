from datetime import date as date_cls
from datetime import datetime, timedelta

from app.models import Booking, Service, ServiceCategory, ServiceSchedule, Location
from authentication.serializers import UserModelSerializer
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CurrentUserDefault, HiddenField, ListField
from rest_framework.serializers import ModelSerializer, TimeField


class ServiceScheduleSerializer(ModelSerializer):
    start_time = TimeField(
        format='%H:%M',
        input_formats=[
            '%H:%M:%S.%fZ',
            '%H:%M:%SZ',
            '%H:%M:%S',
            '%H:%M',
        ],
        allow_null=False
    )
    end_time = TimeField(
        format='%H:%M',
        input_formats=[
            '%H:%M:%S.%fZ',
            '%H:%M:%SZ',
            '%H:%M:%S',
            '%H:%M',
        ],
        allow_null=False
    )

    class Meta:
        model = ServiceSchedule
        fields = ("weekday", "start_time", "end_time")

    def validate(self, data):
        if data["start_time"] >= data["end_time"]:
            raise ValidationError("start_time must be before end_time")
        return data


class ServiceCategoryModelSerializer(ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'

class LocationModelSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = "lat" , "lng", "name"

class ServiceModelSerializer(ModelSerializer):
    owner = HiddenField(default=CurrentUserDefault())
    schedules = ServiceScheduleSerializer(many=True, required=False)
    location = LocationModelSerializer()

    class Meta:
        model = Service
        fields = "id", "name", 'owner', 'duration', "price", "description", "address", "capacity", "category", "schedules" , "location"

    def validate_duration(self, value):
        minutes = value.total_seconds() / 60
        if minutes <= 0 or minutes % 15 != 0:
            raise ValidationError("Duration must be a positive multiple of 15 minutes.")
        return value

    def create(self, validated_data):
        schedules_data = validated_data.pop("schedules", [])
        location_data = validated_data.pop("location", [])
        service = Service.objects.create(**validated_data)
        for sch in schedules_data:
            ServiceSchedule.objects.create(service=service, **sch)
        Location.objects.create(service=service , **location_data)
        return service


class ServiceRetrieveModelSerializer(ModelSerializer):
    category = ServiceCategoryModelSerializer()
    owner = UserModelSerializer()

    class Meta:
        model = Service
        fields = "__all__"


class BookingHistorySerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"


class BookingModelSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    start_time = TimeField(
        format='%H:%M',
        input_formats=[
            '%H:%M:%S.%fZ',
            '%H:%M:%SZ',
            '%H:%M:%S',
            '%H:%M',
        ],
        allow_null=False
    )

    class Meta:
        model = Booking
        fields = ("id", "service", "user", "weekday", "start_time", "duration", "seats")
        read_only_fields = ("id", "user")

    def validate_seats(self, value):
        if value <= 0:
            raise ValidationError("Seats must be greater than 0")
        return value

    def validate(self, data):
        service = data["service"]
        seats = data.get("seats", 1)
        weekday = data["weekday"]
        start_time = data["start_time"]
        duration = data.get("duration", service.duration)

        if seats > service.capacity:
            raise ValidationError("Seats can't exceed service capacity")

        end_time = (datetime.combine(date_cls.min, start_time) + duration).time()

        schedule_match = service.schedules.filter(
            weekday=weekday,
            start_time__lte=start_time,
            end_time__gte=end_time
        ).exists()

        if not schedule_match:
            raise ValidationError("Service is closed at that time")

        return data

    def create(self, validated_data):
        user = validated_data.pop("user", self.context["request"].user)
        service = validated_data["service"]
        weekday = validated_data["weekday"]
        start_time = validated_data["start_time"]
        duration = validated_data.get("duration", service.duration)
        seats = validated_data.get("seats", 1)

        start_dt = datetime.combine(date_cls.min, start_time)
        end_time = (start_dt + duration).time()

        with transaction.atomic():
            # TODO fix filter
            # filter(start_time__gte=booking_start_time, end_time__lt=booking_start_time)
            overlapping = Booking.objects.select_for_update().filter(
                service=service,
                weekday=weekday,
                start_time__lt=end_time,
                duration__gt=timedelta(0)
            )

            total_booked = overlapping.aggregate(total=Coalesce(Sum("seats"), 0))["total"] or 0

            if total_booked + seats > service.capacity:
                raise ValidationError("Not enough capacity for this time slot")

            booking = Booking.objects.create(
                service=service,
                user=user,
                weekday=weekday,
                start_time=start_time,
                duration=duration,
                seats=seats
            )

        return booking
