
import pytest
from app.models import ServiceCategory
from django.test import TestCase  # noqa


@pytest.fixture
def category(client):
    return ServiceCategory.objects.create(name='Category 1')


@pytest.mark.django_db
def test_category(category, client):
    category_count = ServiceCategory.objects.count()

    assert category_count == 1
