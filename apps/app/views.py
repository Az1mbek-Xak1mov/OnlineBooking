from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.transaction import atomic
from django.shortcuts import render  # noqa
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, ListAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from app.models import Service, Booking, ServiceCategory
from app.permissions import IsProvider
from app.serializers import ServiceModelSerializer, BookingSerializer, ServiceRetrieveModelSerializer, \
    ServiceCategoryModelSerializer, BookingHistorySerializer


@extend_schema(tags=['Service'])
class ServiceListCreateAPIView(ListCreateAPIView):
    queryset = Service.objects.select_related("owner", "category")
    serializer_class = ServiceModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProvider]


@extend_schema(tags=['Booking'])
class BookingCreateAPIView(CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.validated_data["service"]
        date_obj = serializer.validated_data["weekday"]
        start_time = serializer.validated_data["start_time"]
        seats = serializer.validated_data.get("seats", 1)
        user = request.user

        with atomic():
            agg = Booking.objects.select_for_update().filter(
                service=service, weekday=date_obj, start_time__lte=start_time, end_time__gte=start_time
            ).aggregate(total=Coalesce(Sum("seats"), 0))
            booked = agg["total"] or 0
            if booked + seats > service.capacity:
                return Response(
                    {"detail": "Not enough capacity for this time slot"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            booking = Booking.objects.create(
                service=service,
                user=user,
                weekday=date_obj,
                start_time=start_time,
                seats=seats
            )

        out = BookingSerializer(booking, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Service'])
class ServiceRetrieveAPIView(RetrieveAPIView):
    serializer_class = ServiceRetrieveModelSerializer
    queryset = Service.objects.all()
    lookup_field = 'pk'


@extend_schema(tags=['Service'])
class ServiceCategoryListAPIView(ListAPIView):
    serializer_class = ServiceCategoryModelSerializer
    queryset = ServiceCategory.objects.all()


@extend_schema(tags=['Booking'])
class UserBookingHistoryListAPIView(ListAPIView):
    serializer_class = BookingHistorySerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Booking.objects.filter(user=user)
