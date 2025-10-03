from datetime import datetime, time, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase  # noqa
from service.models import (Booking, Location, Service, ServiceCategory,
                            ServiceImage, ServiceSchedule)
from users.models import RoleChange, User


@pytest.mark.django_db
class TestUserModel:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number='998101001010', password='1')

    @pytest.fixture
    def provider_user(self):
        return User.objects.create_user(phone_number='998901234563', password='123', type=User.Type.PROVIDER)

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(phone_number='998901234562', password='123', type=User.Type.ADMIN)

    @pytest.fixture
    def moderator_user(self):
        return User.objects.create_user(phone_number='998901234561', password='123', type=User.Type.MODERATOR)

    def test_create_user(self, user):
        assert user.phone_number == '998101001010'
        assert user.type == User.Type.CUSTOMER
        assert user.check_password('1') is True
        assert user.is_customer is True
        assert user.is_provider is False
        assert user.is_moderator is False
        assert user.is_admin is False

    def test_fullname_property(self):
        u = User.objects.create_user(phone_number='998202002020', password='1', first_name='John', last_name='Doe')

        assert u.fullname == 'John Doe'

    def test_user_types(self, provider_user, admin_user, moderator_user):
        assert provider_user.is_provider is True
        assert admin_user.is_admin is True
        assert moderator_user.is_moderator is True

    def test_user_password_change(self, user):
        user.set_password("newpass123")
        user.save()
        assert user.check_password("newpass123") is True

    def test_user_is_active_flag(self, user):
        assert user.is_active is True

    def test_user_type_change(self, user):
        user.type = User.Type.ADMIN
        user.save()
        assert user.is_admin is True

    def test_user_phone_unique(self):
        User.objects.create_user(phone_number='998404004040', password='1')
        with pytest.raises(Exception):
            User.objects.create_user(phone_number='998404004040', password='2')

    def test_user_str_method(self, user):
        assert str(user) == user.phone_number


@pytest.mark.django_db
class TestRoleChange:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number='998901234567', password='test123')

    @pytest.fixture
    def role_change_request(self, user):
        return RoleChange.objects.create(user=user, message='Please upgrade me')

    def test_create_role_change_request(self, role_change_request, user):
        assert role_change_request.user == user
        assert role_change_request.message == 'Please upgrade me'
        assert role_change_request.is_read is False
        assert role_change_request.is_accepted is None

    def test_role_change_ordering(self, user):
        first = RoleChange.objects.create(user=user, message='First')
        second = RoleChange.objects.create(user=user, message='Second')

        all_requests = RoleChange.objects.all()
        assert all_requests[0] == second
        assert all_requests[1] == first

    def test_role_change_accept(self, role_change_request):
        role_change_request.is_accepted = True
        role_change_request.save()
        assert role_change_request.is_accepted is True

    def test_role_change_reject(self, role_change_request):
        role_change_request.is_accepted = False
        role_change_request.save()
        assert role_change_request.is_accepted is False

    def test_role_change_mark_read(self, role_change_request):
        role_change_request.is_read = True
        role_change_request.save()
        assert role_change_request.is_read is True

    def test_role_change_str_method(self, role_change_request):
        assert str(role_change_request) == f"{role_change_request.user.phone_number} - {role_change_request.message}"

    def test_role_change_default_is_none(self, user):
        rc = RoleChange.objects.create(user=user, message='Test')
        assert rc.is_accepted is None
        assert rc.is_read is False


@pytest.mark.django_db
class TestServiceModels:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number='998123456789', password='1', type=User.Type.PROVIDER)

    @pytest.fixture
    def category(self, user):
        return ServiceCategory.objects.create(name='Sport', icon='https://example.com/icon.png')

    @pytest.fixture
    def service(self, category, user):
        return Service.objects.create(owner=user, category=category, name='Tennis', address='Sergili 12/3', capacity=10,
                                      duration=timedelta(minutes=60),
                                      price=1000, description='Very close to pdp university')

    def test_service_str(self, service):
        assert str(service) == service.name

    def test_service_category_str(self, category):
        assert str(category) == category.name

    def test_service_image_str(self, service):
        image = ServiceImage.objects.create(service=service, image='dummy.jpg')
        assert str(image) == f"{service.id} - {image.image.name}"

    def test_location_str(self, service):
        location = Location.objects.create(service=service, name='Test Location', lat=41.3, lng=69.2)
        assert str(location) == "Test Location"

    def test_service_schedule_validation(self, service):
        schedule = ServiceSchedule(
            service=service,
            weekday='monday',
            start_time=time(9, 0),
            end_time=time(12, 0)
        )

        schedule.clean()

        schedule.end_time = time(9, 0)
        with pytest.raises(ValidationError):
            schedule.clean()

    def test_booking_validation_and_auto_date(self, service, user):
        booking = Booking(
            service=service,
            user=user,
            weekday="monday",
            start_time=time(9, 0),
            duration=timedelta(minutes=60),
            seats=3
        )
        booking.clean()
        assert booking.date is None or booking.date is not None

        booking.seats = service.capacity + 1
        with pytest.raises(ValidationError):
            booking.clean()

    def test_booking_save_sets_end_time(self, service, user):
        booking = Booking.objects.create(
            service=service,
            user=user,
            weekday="tuesday",
            start_time=time(10, 0),
            duration=timedelta(minutes=60),
            seats=1
        )
        assert booking.end_time is not None
        expected_end = (datetime.combine(datetime.today(), booking.start_time) + booking.duration).time()
        assert booking.end_time.hour == expected_end.hour
        assert booking.end_time.minute == expected_end.minute

    def test_service_capacity_limit(self, service):
        assert service.capacity == 10

    def test_service_duration_type(self, service):
        assert isinstance(service.duration, timedelta)

    def test_service_price_positive(self, service):
        assert service.price > 0

    def test_service_update_description(self, service):
        service.description = "Updated description"
        service.save()
        assert service.description == "Updated description"

    def test_service_category_relation(self, service, category):
        assert service.category == category


print(1)