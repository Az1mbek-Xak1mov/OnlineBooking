from app.models import Booking, Service, ServiceCategory
from app.permissions import IsProvider
from app.serializers import (BookingHistorySerializer, BookingModelSerializer,
                             ServiceCategoryModelSerializer,
                             ServiceModelSerializer,
                             ServiceRetrieveModelSerializer)
from django.shortcuts import render  # noqa
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     ListCreateAPIView, RetrieveAPIView)
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)


@extend_schema(tags=['Service'])
class ServiceListCreateAPIView(ListCreateAPIView):
    queryset = Service.objects.select_related("owner", "category")
    serializer_class = ServiceModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProvider]


@extend_schema(tags=['Booking'])
class BookingCreateAPIView(CreateAPIView):
    serializer_class = BookingModelSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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


@extend_schema(tags=['Booking'])
class UserBookingHistoryListAPIView(ListAPIView):
    serializer_class = BookingHistorySerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)
