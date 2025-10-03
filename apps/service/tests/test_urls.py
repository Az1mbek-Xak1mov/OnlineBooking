import uuid
from datetime import timedelta

import pytest
from django.test import TestCase  # noqa
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from service.models import Service
from users.models import User


@pytest.mark.django_db
def test_registration_url(client):
    url = reverse_lazy('register')

    assert url.startswith('/api/v1/auth/registration/')
    assert 'registration' in url

    response = client.get(url)
    assert response.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_200_OK]

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.django_db
def test_verify_phone_number_url(client):
    url = reverse_lazy('verify_phone_number')

    assert url.startswith('/api/v1/auth/registration/verify/phone_number/')
    assert 'verify' in url

    response = client.get(url)
    assert response.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_200_OK]

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.django_db
def test_login_url(client):
    url = reverse_lazy('login')

    assert url.startswith('/api/v1/')
    assert 'login' in url

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_token_refresh_url(client):
    url = reverse_lazy('token_refresh')

    assert url.startswith('/api/v1/')
    assert 'refresh' in url

    response = client.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_me_url(client):
    url = reverse_lazy('get-me')

    assert url.startswith('/api/v1/')
    assert 'get-me' in url

    response = client.get(url)
    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_role_change_request_url(client):
    url = reverse_lazy('role-change')

    assert url.startswith('/api/v1/auth/')
    assert 'role-change-request' in url

    response = client.get(url)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED]

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_my_requests_url(client):
    url = reverse_lazy('my-requests')

    assert url.startswith('/api/v1/')
    assert 'my-requests' in url

    response = client.get(url)
    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_detail_url(client):
    user = User.objects.create_user(phone_number='998101001010', password='1', type='provider')
    url = reverse_lazy('user-detail', kwargs={'pk': user.pk})

    assert url.startswith('/api/v1/auth/')
    assert str(user.pk) in url

    response = client.get(url)
    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.patch(url)
    assert response.request['REQUEST_METHOD'] == 'PATCH'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.delete(url)
    assert response.request['REQUEST_METHOD'] == 'DELETE'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_category_url(client):
    url = reverse_lazy('service-category-list')
    response = client.get(url)

    assert url == '/api/v1/category/services/'
    assert url.startswith('/api/v1/')
    assert url.endswith('/')
    assert 'category' in url
    assert 'services' in url

    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.request['PATH_INFO'] == url
    assert response.wsgi_request.path == url

    data = response.json()
    assert isinstance(data, dict)
    assert 'results' in data
    assert isinstance(data['results'], list)
    assert 'count' in data and isinstance(data['count'], int)


@pytest.mark.django_db
def test_service_create_url(client):
    url = reverse_lazy('service-create')
    response = client.post(url)

    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.request['PATH_INFO'] == url
    assert response.wsgi_request.path == url

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert isinstance(data, dict)
    assert 'detail' in data
    assert data["detail"] == "Authentication credentials were not provided."


@pytest.mark.django_db
def test_service_list_url(client):
    url = reverse_lazy('service-create')

    assert url.startswith('/api/v1/services/')
    assert url.endswith('/')

    response = client.get(url)

    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    if isinstance(data, dict) and 'results' in data:
        assert isinstance(data['results'], list)
        assert 'count' in data and isinstance(data['count'], int)
        assert 'next' in data
        assert 'previous' in data
    else:
        assert isinstance(data, list)

    user = User.objects.create_user(phone_number='998101001010', password='1', type='provider')
    Service.objects.create(name='Test Service', owner=user, duration=timedelta(minutes=30), price=100)
    response2 = client.get(url)
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()
    if 'results' in data2:
        assert any('Test Service' in str(item.values()) for item in data2['results'])
    else:
        assert any('Test Service' in str(item.values()) for item in data2)


@pytest.mark.django_db
def test_service_delete_url(client):
    service_id = uuid.uuid4()
    url = reverse_lazy('service-detail', kwargs={"pk": service_id})
    response = client.delete(url)

    assert url.startswith('/api/v1/services/')
    assert str(service_id) in url
    assert url.endswith('/')

    assert response.request['REQUEST_METHOD'] == 'DELETE'

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    assert isinstance(response.data, dict)


@pytest.mark.django_db
def test_service_update_url(client):
    service_id = uuid.uuid4()
    url = reverse_lazy('service-detail', kwargs={"pk": service_id})
    payload = {"name": "Updated name"}
    response = client.patch(url, data=payload, content_type="application/json")

    assert url.startswith('/api/v1/services/')
    assert str(service_id) in url
    assert url.endswith('/')

    assert response.request['REQUEST_METHOD'] == 'PATCH'

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    assert isinstance(response.data, dict)


@pytest.mark.django_db
def test_service_detail_url(client):
    service_id = uuid.uuid4()
    url = reverse_lazy('service-detail', kwargs={"pk": service_id})
    response = client.get(url)

    assert url.startswith('/api/v1/services/')
    assert str(service_id) in url
    assert url.endswith('/')

    assert response.request['REQUEST_METHOD'] == 'GET'

    assert isinstance(response.data, dict)


@pytest.mark.django_db
def test_my_services_url(client):
    url = reverse_lazy('my-services-list')
    response = client.get(url)

    assert url == '/api/v1/services/my-services/'
    assert url.startswith('/api/v1/services/')
    assert url.endswith('/')
    assert 'my-services' in url

    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.request['PATH_INFO'] == url
    assert response.wsgi_request.path == url

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    assert 'Content-Type' in response.headers
    assert response.headers['Content-Type'].startswith('application/json')

    data = response.json()
    assert 'detail' in data


@pytest.mark.django_db
def test_booking_create_url(client):
    url = reverse_lazy('booking-create')
    assert url.startswith('/api/v1/')
    assert 'bookings' in url

    response = client.get(url)
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED]

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_users_booking_pending_url(client):
    url = reverse_lazy('users-booking-history-pending')
    assert url.startswith('/api/v1/')
    assert 'booking' in url
    assert 'pending' in url

    response = client.get(url)
    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.status_code == status.HTTP_200_OK

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_users_booking_history_url(client):
    url = reverse_lazy('users-booking-history')
    assert url.startswith('/api/v1/')
    assert 'booking' in url
    assert 'history' in url

    response = client.get(url)
    assert response.request['REQUEST_METHOD'] == 'GET'
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(url)
    assert response.request['REQUEST_METHOD'] == 'POST'
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED]


print(1)