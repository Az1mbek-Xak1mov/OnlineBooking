from datetime import timedelta
import pytest
from django.urls import reverse_lazy
from rest_framework import status
from service.models import ServiceCategory, Service
from users.models import User


@pytest.mark.django_db
class TestServiceCategoryListAPIView:

    @pytest.fixture
    def category(self):
        return ServiceCategory.objects.create(name="Sport", icon="https://example.com/icon.png")

    def test_list_categories(self, client, category):
        url = reverse_lazy("service-category-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == category.name


@pytest.mark.django_db
class TestMyServicesListApiView:

    @pytest.fixture
    def provider_user(self):
        return User.objects.create_user(phone_number="998900000001", password="1", type=User.Type.PROVIDER)

    @pytest.fixture
    def category(self):
        return ServiceCategory.objects.create(name="Education")

    @pytest.fixture
    def service(self, provider_user, category):
        return Service.objects.create(
            owner=provider_user,
            category=category,
            name="Math Course",
            address="Main Street 1",
            capacity=10,
            duration=timedelta(minutes=60),
            price=20000,
            description="Learn Math"
        )

    def test_list_my_services(self, client, provider_user, service):
        client.force_login(provider_user)
        url = reverse_lazy("my-services-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Math Course"

    def test_unauthenticated_access_denied(self, client):
        url = reverse_lazy("my-services-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestServiceListCreateAPIView:

    @pytest.fixture
    def provider_user(self):
        return User.objects.create_user(phone_number="998900000002", password="1", type=User.Type.PROVIDER)

    @pytest.fixture
    def category(self):
        return ServiceCategory.objects.create(name="Beauty")

    def test_list_services(self, client, provider_user, category):
        Service.objects.create(
            owner=provider_user,
            category=category,
            name="Haircut",
            address="Salon 1",
            capacity=3,
            duration=timedelta(minutes=30),
            price=5000,
            description="Haircut service"
        )
        url = reverse_lazy("service-create")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "Haircut"

    def test_create_service(self, client, provider_user, category):
        client.force_login(provider_user)
        url = reverse_lazy("service-create")
        payload = {
            "name": "Makeup",
            "category": str(category.id),
            "duration": "00:30:00",
            "price": 10000,
            "address": "Salon 2",
            "capacity": 5,
            "description": "Evening makeup",
            "images": []
        }
        response = client.post(url, payload, content_type="application/json")
        print(response.json())
        assert response.status_code == status.HTTP_201_CREATED
        assert Service.objects.filter(name="Makeup").exists()


@pytest.mark.django_db
class TestPendingBookingListAPIView:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998900000005", password="1", type=User.Type.CUSTOMER)

    def test_unauthenticated_gets_empty(self, client):
        url = reverse_lazy("users-booking-history-pending")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_authenticated_user_pending_list(self, client, user):
        client.force_login(user)
        url = reverse_lazy("users-booking-history-pending")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["results"], list)


@pytest.mark.django_db
class TestUserBookingHistoryListAPIView:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998900000006", password="1", type=User.Type.CUSTOMER)

    def test_requires_authentication(self, client):
        url = reverse_lazy("users-booking-history")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_empty_history(self, client, user):
        client.force_login(user)
        url = reverse_lazy("users-booking-history")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

