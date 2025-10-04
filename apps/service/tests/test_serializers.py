from datetime import time, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from service.models import ServiceCategory, ServiceSchedule, Service, Booking
from service.serializers import ServiceScheduleSerializer, ServiceModelSerializer, BookingModelSerializer
from users.models import RoleChange, User
from users.serializers import (CustomTokenObtainPairSerializer,
                               MyRequestsModelSerializer,
                               RoleChangeModelSerializer, UserCreateSerializer,
                               UserModelSerializer, UserRegistrationSerializer,
                               VerifyOtpSerializer)

VALID_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80'
    b'\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04'
    b'\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01'
    b'\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B'
)


@pytest.mark.django_db
class TestUserRegistrationSerializer:

    @pytest.fixture
    def user_data(self):
        return {
            "phone_number": "998123456789",
            "password": "test123",
            "confirm_password": "test123",
            "first_name": "John",
            "last_name": "Doe"
        }

    def test_validate_phone_number_success(self, user_data):
        serializer = UserRegistrationSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["phone_number"] == "998123456789"

    def test_validate_phone_number_invalid_prefix(self, user_data):
        user_data["phone_number"] = "997123456789"
        serializer = UserRegistrationSerializer(data=user_data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate_password_mismatch(self, user_data):
        user_data["confirm_password"] = "wrong"
        serializer = UserRegistrationSerializer(data=user_data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "Confirm Password" in exc_info.value.detail

    def test_create_user(self, user_data):
        serializer = UserRegistrationSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert isinstance(user, User)
        assert user.phone_number == "998123456789"


@pytest.mark.django_db
class TestUserCreateSerializer:

    @pytest.fixture
    def user_data(self):
        return {
            "phone_number": "998987654321",
            "password": "test123",
            "first_name": "Alice",
            "last_name": "Smith"
        }

    def test_create_user_sets_password(self, user_data):
        serializer = UserCreateSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert user.check_password("test123")
        assert user.first_name == "Alice"


@pytest.mark.django_db
class TestVerifyOtpSerializer:

    def test_validate_phone_number_success(self):
        serializer = VerifyOtpSerializer(data={"phone_number": "998123456789", "otp_code": "123456"})
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["phone_number"] == "998123456789"

    def test_validate_phone_number_invalid(self):
        serializer = VerifyOtpSerializer(data={"phone_number": "12345", "otp_code": "123456"})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998101010101", password="test123")

    def test_validate_returns_users_info(self, user):
        serializer = CustomTokenObtainPairSerializer(data={"phone_number": user.phone_number, "password": "test123"})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        assert "users" in data
        assert data["users"]["phone_number"] == user.phone_number


@pytest.mark.django_db
class TestUserModelSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998202020202", password="test123", first_name="Bob",
                                        last_name="Lee")

    def test_serialization(self, user):
        serializer = UserModelSerializer(user)
        data = serializer.data
        assert data["phone_number"] == user.phone_number
        assert data["first_name"] == "Bob"


@pytest.mark.django_db
class TestRoleChangeModelSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998303030303", password="test123")

    @pytest.fixture
    def role_change_data(self):
        return {"message": "Upgrade me"}

    def test_create_role_change(self, user, role_change_data):
        serializer = RoleChangeModelSerializer(data=role_change_data,
                                               context={"request": type("Request", (), {"user": user})()})
        serializer.is_valid(raise_exception=True)
        role_change = serializer.save()
        assert role_change.user == user
        assert role_change.message == "Upgrade me"
        assert role_change.is_read is False
        assert role_change.is_accepted is None


@pytest.mark.django_db
class TestMyRequestsModelSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998404040404", password="test123")

    @pytest.fixture
    def role_change(self, user):
        return RoleChange.objects.create(user=user, message="Request 1")

    def test_serialization(self, role_change):
        serializer = MyRequestsModelSerializer(role_change)
        data = serializer.data
        assert data["message"] == "Request 1"
        assert data["user"] == role_change.user.id


@pytest.mark.django_db
class TestServiceScheduleSerializer:
    def test_valid_schedule(self):
        data = {"weekday": "monday", "start_time": "10:00", "end_time": "12:00"}
        ser = ServiceScheduleSerializer(data=data)
        assert ser.is_valid(), ser.errors
        assert ser.validated_data["start_time"].hour == 10

    def test_invalid_equal_time(self):
        data = {"weekday": "monday", "start_time": "10:00", "end_time": "10:00"}
        ser = ServiceScheduleSerializer(data=data)
        assert not ser.is_valid()
        assert "start_time must be before end_time" in str(ser.errors)

    def test_invalid_start_after_end(self):
        data = {"weekday": "monday", "start_time": "12:00", "end_time": "10:00"}
        ser = ServiceScheduleSerializer(data=data)
        assert not ser.is_valid()
        assert "start_time must be before end_time" in str(ser.errors)

    def test_invalid_format(self):
        data = {"weekday": "monday", "start_time": "12.00", "end_time": "13.00"}
        ser = ServiceScheduleSerializer(data=data)
        assert not ser.is_valid()
        assert "start_time" in ser.errors or "end_time" in ser.errors


@pytest.mark.django_db
class TestServiceModelSerializer:
    def setup_method(self):
        self.user = User.objects.create_user(phone_number="998101001010", password="12345")
        self.category = ServiceCategory.objects.create(name="Test Category")
        self.context = {"request": type("Req", (), {"user": self.user})()}

    def test_create_full_valid(self):
        image = SimpleUploadedFile("test.jpg", VALID_IMAGE, content_type="image/jpeg")

        data = {
            "name": "Full Service",
            "duration": "1:00:00",
            "price": 10000,
            "description": "desc",
            "address": "Tashkent",
            "capacity": 5,
            "category": str(self.category.id),
            "images": [image],
            "location": {"lat": 41.3, "lng": 69.2, "name": "Center"},
            "schedules": [
                {"weekday": "monday", "start_time": "09:00", "end_time": "18:00"},
                {"weekday": "tuesday", "start_time": "09:00", "end_time": "18:00"},
            ],
        }

        ser = ServiceModelSerializer(data=data, context=self.context)
        ser.initial_data = data
        assert ser.is_valid(), ser.errors
        instance = ser.save()

        assert instance.images.count() == 1
        assert instance.schedules.count() == 2
        assert instance.location.name == "Center"

    def test_invalid_duration(self):
        data = {
            "name": "Invalid Duration",
            "duration": "0:07:00",
            "price": 5000,
            "description": "Bad",
            "address": "Loc",
            "capacity": 2,
            "category": str(self.category.id),
        }
        ser = ServiceModelSerializer(data=data, context=self.context)
        assert not ser.is_valid()
        assert "Duration must be a positive multiple" in str(ser.errors)

    def test_location_json_string(self):
        image = SimpleUploadedFile("test.jpg", VALID_IMAGE, content_type="image/jpeg")
        data = {
            "name": "Test JSON loc",
            "duration": "1:00:00",
            "price": 10000,
            "description": "desc",
            "address": "Tashkent",
            "capacity": 5,
            "category": str(self.category.id),
            "images": [image],
        }
        ser = ServiceModelSerializer(data=data, context=self.context)
        ser.initial_data = {
            **data,
            "location": '{"lat": 41.0, "lng": 69.0, "name": "JSON Center"}'
        }
        assert ser.is_valid(), ser.errors
        instance = ser.save()
        assert instance.location.name == "JSON Center"

    def test_schedules_as_string_list(self):
        image = SimpleUploadedFile("test.jpg", VALID_IMAGE, content_type="image/jpeg")
        data = {
            "name": "StringSchedule",
            "duration": "1:00:00",
            "price": 10000,
            "description": "desc",
            "address": "Tashkent",
            "capacity": 5,
            "category": str(self.category.id),
            "images": [image],
        }
        schedules_str = '[{"weekday": "monday", "start_time": "10:00", "end_time": "12:00"}]'
        ser = ServiceModelSerializer(data=data, context=self.context)
        ser.initial_data = {**data, "schedules": schedules_str}
        assert ser.is_valid(), ser.errors
        service = ser.save()
        assert service.schedules.count() == 1


@pytest.mark.django_db
class TestBookingModelSerializer:
    def setup_method(self):
        self.user = User.objects.create_user(phone_number="998101001010", password="12345")
        self.context = {"request": type("Req", (), {"user": self.user})()}

    def _create_service_with_schedule(self, capacity=5):
        category = ServiceCategory.objects.create(name="BookingCat")
        service = Service.objects.create(
            owner=self.user,
            name="Service",
            duration=timedelta(minutes=30),
            price=10000,
            description="desc",
            address="address",
            capacity=capacity,
            category=category
        )
        ServiceSchedule.objects.create(
            service=service,
            weekday="monday",
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        return service

    def test_valid_booking(self):
        service = self._create_service_with_schedule()
        data = {
            "service": service.id,
            "weekday": "monday",
            "start_time": "10:00",
            "duration": "0:30:00",
            "seats": 2,
        }
        ser = BookingModelSerializer(data=data, context=self.context)
        assert ser.is_valid(), ser.errors
        booking = ser.save()
        assert booking.seats == 2

    def test_exceeds_capacity(self):
        service = self._create_service_with_schedule(capacity=2)
        Booking.objects.create(
            user=self.user,
            service=service,
            weekday="monday",
            start_time=time(10, 0),
            end_time=time(10, 30),
            seats=2
        )

        data = {
            "service": service.id,
            "weekday": "monday",
            "start_time": "10:00",
            "duration": "0:30:00",
            "seats": 1,
        }
        ser = BookingModelSerializer(data=data, context=self.context)
        assert ser.is_valid(), ser.errors
        with pytest.raises(ValidationError) as excinfo:
            ser.save()
        assert "Not enough capacity" in str(excinfo.value)

    def test_closed_time(self):
        category = ServiceCategory.objects.create(name="ClosedCat")
        service = Service.objects.create(
            owner=self.user,
            name="Closed",
            duration=timedelta(minutes=30),
            price=10000,
            description="desc",
            address="addr",
            capacity=5,
            category=category
        )
        ServiceSchedule.objects.create(
            service=service,
            weekday="monday",
            start_time=time(9, 0),
            end_time=time(10, 0)
        )

        data = {
            "service": service.id,
            "weekday": "monday",
            "start_time": "11:00",
            "duration": "0:30:00",
            "seats": 1,
        }
        ser = BookingModelSerializer(data=data, context=self.context)
        assert not ser.is_valid()
        assert "Service is closed" in str(ser.errors)

    def test_invalid_seats(self):
        service = self._create_service_with_schedule()
        data = {
            "service": service.id,
            "weekday": "monday",
            "start_time": "09:00",
            "duration": "0:30:00",
            "seats": 0,
        }
        ser = BookingModelSerializer(data=data, context=self.context)
        assert not ser.is_valid()
        assert "Seats must be greater" in str(ser.errors)
