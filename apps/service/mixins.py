from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter


class FilterSearchMixin:
    filter_backends = (DjangoFilterBackend, SearchFilter)


print(1)