import json
from datetime import date as date_cls
from datetime import datetime

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (CurrentUserDefault, HiddenField, ImageField, ListField)
from rest_framework.serializers import ModelSerializer, TimeField, Serializer
from service.models import (Booking, Location, Service, ServiceCategory,
                            ServiceImage, ServiceSchedule)


class ServiceCategoryModelSerializer(ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'


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


class ServiceImageModelSerializer(ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = 'image',


class LocationModelSerializer(ModelSerializer):
    class Meta:
        model = Location
        fields = ('lat', 'lng', 'name')


class ServiceModelSerializer(ModelSerializer):
    owner = HiddenField(default=CurrentUserDefault())
    location = LocationModelSerializer(required=False)
    images = ListField(child=ImageField(), write_only=True)
    schedules = ServiceScheduleSerializer(many=True, required=False)

    class Meta:
        model = Service
        fields = ("id", "name", 'owner', 'duration', "price", "description", "address", "capacity", "category",
                  "images", "location", "schedules")

    def validate_duration(self, value):
        minutes = value.total_seconds() / 60
        if minutes <= 0 or minutes % 15 != 0:
            raise ValidationError("Duration must be a positive multiple of 15 minutes.")
        return value

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        location_data = validated_data.pop("location", None)
        schedules_data = validated_data.pop("schedules", [])

        if not location_data:
            raw_loc = self.initial_data.get('location')
            if raw_loc and isinstance(raw_loc, str):
                try:
                    location_data = json.loads(raw_loc)
                except Exception:
                    location_data = {}
        if not schedules_data:
            raw_schedules = self.initial_data.get('schedules')
            print(raw_schedules, type(raw_schedules))
            if raw_schedules and isinstance(raw_schedules, str):
                print(len(raw_schedules))
                s = raw_schedules.strip()
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        schedules_data = parsed
                    elif isinstance(parsed, dict):
                        schedules_data = [parsed]
                    else:
                        schedules_data = []
                except Exception:
                    try:
                        parsed = json.loads(f'[{s}]')
                        if isinstance(parsed, list):
                            schedules_data = parsed
                        else:
                            schedules_data = []
                    except Exception:
                        schedules_data = []
                        if '},{' in s:
                            parts = s.split('},{')
                            for i, part in enumerate(parts):
                                if i == 0:
                                    candidate = part + '}'
                                elif i == len(parts) - 1:
                                    candidate = '{' + part
                                else:
                                    candidate = '{' + part + '}'
                                try:
                                    schedules_data.append(json.loads(candidate))
                                except Exception:
                                    pass
                        if not schedules_data:
                            for line in s.splitlines():
                                line = line.strip().rstrip(',')
                                if not line:
                                    continue
                                try:
                                    schedules_data.append(json.loads(line))
                                except Exception:
                                    continue
                        if not schedules_data:
                            schedules_data = []
        service = Service.objects.create(**validated_data)
        for img in images_data:
            ServiceImage.objects.create(service=service, image=img)
        for sch in schedules_data:
            ServiceSchedule.objects.create(service=service, **sch)
        if location_data:
            Location.objects.create(service=service, **location_data)
        return service

    def to_representation(self, instance: Service):
        to_repr = super().to_representation(instance)
        to_repr['images'] = ServiceImageModelSerializer(instance.images.all(), many=True, context=self.context).data
        to_repr['key'] = 'vali'
        return to_repr

    def to_internal_value(self, data):
        data = data.copy()

        loc = data.get("location")
        if isinstance(loc, str):
            try:
                data["location"] = json.loads(loc)
            except json.JSONDecodeError:
                raise ValidationError({
                    "location": "Invalid JSON string"
                })

        sch = data.get("schedules")
        if isinstance(sch, str):
            try:
                data["schedules"] = json.loads(sch)
            except json.JSONDecodeError:
                raise ValidationError({
                    "schedules": "Invalid JSON string"
                })

        return super().to_internal_value(data)


class BookingHistorySerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"


class BookingModelSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())

    start_time = TimeField(
        format='%H:%M',
        input_formats=['%H:%M:%S.%fZ', '%H:%M:%SZ', '%H:%M:%S', '%H:%M'],
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
        weekday = data["weekday"]
        start_time = data["start_time"]
        seats = data.get("seats", 1)
        duration = data.get("duration") or service.duration

        start_dt = datetime.combine(date_cls.min, start_time)
        candidate_end_time = (start_dt + duration).time()

        if seats > service.capacity:
            raise ValidationError("Seats can't exceed service capacity")

        schedule_match = service.schedules.filter(
            weekday=weekday,
            start_time__lte=start_time,
            end_time__gte=candidate_end_time
        ).exists()
        if not schedule_match:
            raise ValidationError("Service is closed at that time")

        service_duration = service.duration
        if duration.total_seconds() % service_duration.total_seconds() != 0:
            raise ValidationError(f"Duration must be a multiple of service duration ({service_duration}).")

        data["duration"] = duration
        return data

    def create(self, validated_data):
        user = validated_data.pop("users", self.context["request"].user)
        service = validated_data["service"]
        weekday = validated_data["weekday"]
        start_time = validated_data["start_time"]
        duration = validated_data["duration"]
        seats = validated_data.get("seats", 1)

        start_dt = datetime.combine(date_cls.min, start_time)
        candidate_end_time = (start_dt + duration).time()

        with transaction.atomic():
            overlapping = Booking.objects.select_for_update().filter(
                service=service,
                weekday=weekday,
                start_time__lt=candidate_end_time,
                end_time__gt=start_time
            )

            total_booked = overlapping.aggregate(
                total=Coalesce(Sum("seats"), 0)
            )["total"] or 0

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


class ServiceUpdateModelSerializer(ModelSerializer):
    owner = HiddenField(default=CurrentUserDefault())
    location = LocationModelSerializer(required=False)
    schedules = ServiceScheduleSerializer(many=True, required=False)

    class Meta:
        model = Service
        fields = ("id", "name", 'owner', 'duration', "price", "description", "address", "capacity", "category",
                  "location", "schedules")

    def update(self, instance, validated_data):
        location_data = validated_data.pop("location", None)
        schedules_data = validated_data.pop("schedules", None)

        if not location_data:
            raw_loc = self.initial_data.get('location')
            if raw_loc and isinstance(raw_loc, str):
                try:
                    location_data = json.loads(raw_loc)
                except Exception:
                    location_data = {}

        if not schedules_data:
            raw_schedules = self.initial_data.get('schedules')
            if raw_schedules and isinstance(raw_schedules, str):
                s = raw_schedules.strip()
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        schedules_data = parsed
                    elif isinstance(parsed, dict):
                        schedules_data = [parsed]
                    else:
                        schedules_data = []
                except Exception:
                    try:
                        parsed = json.loads(f'[{s}]')
                        if isinstance(parsed, list):
                            schedules_data = parsed
                        else:
                            schedules_data = []
                    except Exception:
                        schedules_data = []
                        if '},{' in s:
                            parts = s.split('},{')
                            for i, part in enumerate(parts):
                                if i == 0:
                                    candidate = part + '}'
                                elif i == len(parts) - 1:
                                    candidate = '{' + part
                                else:
                                    candidate = '{' + part + '}'
                                try:
                                    schedules_data.append(json.loads(candidate))
                                except Exception:
                                    pass
                        if not schedules_data:
                            for line in s.splitlines():
                                line = line.strip().rstrip(',')
                                if not line:
                                    continue
                                try:
                                    schedules_data.append(json.loads(line))
                                except Exception:
                                    continue
                        if not schedules_data:
                            schedules_data = []

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if location_data:
            try:
                loc = instance.location
            except Exception:
                loc = getattr(instance, "location", None)
            if loc and getattr(loc, "pk", None):
                for k, v in location_data.items():
                    setattr(loc, k, v)
                loc.save()
            else:
                Location.objects.create(service=instance, **location_data)
        if schedules_data:
            for sch in schedules_data:
                if not isinstance(sch, dict):
                    continue
                weekday = sch.get("weekday")
                start_time = sch.get("start_time")
                end_time = sch.get("end_time")
                if not weekday or start_time is None or end_time is None:
                    continue
                weekday_normalized = str(weekday).lower()
                existing = ServiceSchedule.objects.filter(service=instance, weekday=weekday_normalized).first()
                if existing:
                    existing.start_time = start_time
                    existing.end_time = end_time
                    existing.save(update_fields=["start_time", "end_time"])
                else:
                    ServiceSchedule.objects.create(
                        service=instance,
                        weekday=weekday_normalized,
                        start_time=start_time,
                        end_time=end_time
                    )
        return instance


class BookingSerializer(ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"