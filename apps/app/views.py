from app.models import Booking, Service, ServiceCategory
from app.permissions import IsProvider
from app.serializers import (BookingHistorySerializer, BookingModelSerializer,
                             ServiceCategoryModelSerializer,
                             ServiceModelSerializer,
                             ServiceRetrieveModelSerializer)
from django.shortcuts import render  # noqa
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import SearchFilter
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     ListCreateAPIView, RetrieveAPIView)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)


class MyLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


@extend_schema(tags=['Service'])
class ServiceListCreateAPIView(ListCreateAPIView):
    queryset = Service.objects.select_related("owner", "category")
    serializer_class = ServiceModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProvider]
    parser_classes = (MultiPartParser, FormParser)   


    pagination_class = MyLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = 'created_at',
    search_fields = 'category__name', 'name', 'address', 'capacity', 'price', 'description'


@extend_schema(tags=['Booking'])
class BookingCreateAPIView(CreateAPIView):
    serializer_class = BookingModelSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Service'])
class ServiceRetrieveAPIView(RetrieveAPIView):
    serializer_class = ServiceRetrieveModelSerializer
    queryset = Service.objects.all()
    authentication_classes = ()


@extend_schema(tags=['Service'])
class ServiceCategoryListAPIView(ListAPIView):
    serializer_class = ServiceCategoryModelSerializer
    queryset = ServiceCategory.objects.all()
    authentication_classes = ()
    pagination_class = MyLimitOffsetPagination

    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = 'created_at',
    search_fields = 'name',


@extend_schema(tags=['Booking'])
class UserBookingHistoryListAPIView(ListAPIView):
    serializer_class = BookingHistorySerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]

    pagination_class = MyLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = 'created_at',
    search_fields = 'service__name', 'weekday', 'start_time', 'seats'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)
