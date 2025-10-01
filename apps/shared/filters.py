from service.models import Service
from django_filters import (CharFilter, DateFromToRangeFilter, FilterSet,
                            NumberFilter)


class ServiceFilter(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr="gte")
    max_price = NumberFilter(field_name="price", lookup_expr="lte")
    category = CharFilter(field_name="category__name")
    created_at = DateFromToRangeFilter()

    class Meta:
        model = Service
        fields = ["category", "min_price", "max_price", "created_at"]
