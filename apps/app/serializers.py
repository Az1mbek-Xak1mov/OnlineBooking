from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CurrentUserDefault, HiddenField, ListField
from rest_framework.serializers import ModelSerializer, TimeField

from app.models import Booking, Service, ServiceCategory, ServiceSchedule
from authentication.serializers import UserModelSerializer


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


class ServiceModelSerializer(ModelSerializer):
    owner = HiddenField(default=CurrentUserDefault())
    schedules = ServiceScheduleSerializer(many=True, required=False)

    class Meta:
        model = Service
        fields = ("id", "name", "image", 'owner', "price", "description", "address", "capacity", "category",
                  "schedules")

    def validate_duration(self, value):
        minutes = value.total_seconds() / 60
        if minutes <= 0 or minutes % 15 != 0:
            raise ValidationError("Duration must be a positive multiple of 15 minutes.")
        return value

    def create(self, validated_data):
        schedules_data = validated_data.pop("schedules", [])
        service = Service.objects.create(**validated_data)
        for sch in schedules_data:
            ServiceSchedule.objects.create(service=service, **sch)
        return service


class ServiceRetrieveModelSerializer(ModelSerializer):
    schedules = ServiceScheduleSerializer(many=True)
    free_time = ListField(default=list())
    category = ServiceCategoryModelSerializer()
    owner = UserModelSerializer()

    class Meta:
        model = Service
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
        fields = ("id", "service", "user", "weekday", "start_time", "seats")
        read_only_fields = ("id", "user")

    def validate_seats(self, value):
        if value <= 0:
            raise ValidationError("seats must be more than 1")
        return value

    def validate(self, data):
        service = data["service"]
        seats = data.get("seats", 1)
        if seats > service.capacity:
            raise ValidationError("seats can't exceed service capacity")

        weekday = data["weekday"]
        start_time = data["start_time"]

        matches = service.schedules.filter(
            weekday=weekday,
            start_time__lte=start_time,
            end_time__gt=start_time
        )
        if not matches.exists():
            raise ValidationError("Service is closed at that time")

        return data

    def create(self, validated_data):
        user = validated_data.pop("user", self.context["request"].user)
        service = validated_data["service"]
        weekday = validated_data["weekday"]
        start_time = validated_data["start_time"]
        seats = validated_data.get("seats", 1)

        with transaction.atomic():
            agg = Booking.objects.select_for_update().filter(
                service=service,
                weekday=weekday,
                start_time__lte=start_time,
                end_time__gte=start_time
            ).aggregate(total=Coalesce(Sum("seats"), 0))
            booked = agg["total"] or 0

            if booked + seats > service.capacity:
                raise ValidationError("Not enough capacity for this time slot")

            booking = Booking.objects.create(
                service=service,
                user=user,
                weekday=weekday,
                start_time=start_time,
                seats=seats
            )
        return booking


class BookingHistorySerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
