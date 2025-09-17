from datetime import datetime, date, timedelta

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer,TimeField

from app.models import ServiceSchedule, Booking, Service, ServiceCategory


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

class ServiceSerializer(ModelSerializer):
    schedules = ServiceScheduleSerializer(many=True, required=False)

    class Meta:
        model = Service
        fields = ("id", "owner","name","price","description" ,"address", "capacity", "category", "schedules")
        read_only_fields = ("id",)

    def create(self, validated_data):
        schedules_data = validated_data.pop("schedules", [])
        service = Service.objects.create(**validated_data)
        for sch in schedules_data:
            ServiceSchedule.objects.create(service=service, **sch)
        return service

    def validate(self, data):
        return data


class BookingSerializer(ModelSerializer):
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
        matches = service.schedules.filter(weekday=weekday,
                                           start_time__lte=start_time,
                                           end_time__gt=start_time)
        if not matches.exists():
            raise ValidationError("Service is closed at that time")

        return data

class ServiceRetrieveModelSerializer(ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"

class ServiceCategoryModelSerializer(ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'

class BookingHistorySerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
