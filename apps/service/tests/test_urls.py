import uuid

import pytest
from django.test import TestCase  # noqa
from rest_framework import status
from rest_framework.reverse import reverse_lazy


@pytest.mark.django_db
def test_category_url(client):
    url = reverse_lazy('service-category-list')
    response = client.get(url)

    assert url == '/api/v1/category/services/'
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_service_delete_url(client):
    service_id = uuid.uuid4()
    url = reverse_lazy('service-delete', kwargs={"pk": service_id})
    response = client.delete(url)

    assert url.startswith('/api/v1/services/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
