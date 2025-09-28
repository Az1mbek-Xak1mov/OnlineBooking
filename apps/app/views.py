from datetime import datetime, timezone
from tkinter import Image

from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from app.mixins import FilterSearchMixin
from app.models import Booking, Service, ServiceCategory
from app.permissions import IsProvider
from app.serializers import (BookingHistorySerializer, BookingModelSerializer,
                             ServiceCategoryModelSerializer,
                             ServiceModelSerializer,
                             ServiceRetrieveModelSerializer)
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     ListCreateAPIView, RetrieveAPIView,
                                     get_object_or_404, DestroyAPIView)
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from shared.filters import ServiceFilter
from shared.paginations import CustomLimitOffsetPagination


@extend_schema(tags=['Service'])
class ServiceCategoryListAPIView(FilterSearchMixin, ListAPIView):
    serializer_class = ServiceCategoryModelSerializer
    queryset = ServiceCategory.objects.all()
    authentication_classes = ()

    pagination_class = CustomLimitOffsetPagination
    filterset_fields = 'name',
    search_fields = 'name',


@extend_schema(tags=['Service'])
class MyServicesListApiView(ListAPIView):
    serializer_class = ServiceModelSerializer
    queryset = Service.objects.all()
    permission_classes = IsProvider,

    def get_queryset(self):
        qs = super().get_queryset()

        return qs.filter(owner=self.request.user)


@extend_schema(tags=['Service'])
class ServiceListCreateAPIView(FilterSearchMixin, ListCreateAPIView):
    queryset = Service.objects.select_related("owner", "category")
    serializer_class = ServiceModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProvider]

    pagination_class = CustomLimitOffsetPagination
    filterset_class = ServiceFilter
    search_fields = 'category', 'name', 'address', 'capacity', 'price', 'description'

    def get_queryset(self):
        print(self.request.user)
        return super().get_queryset()


@extend_schema(tags=["Service"])
class ServiceDeleteAPIView(DestroyAPIView):
    serializer_class = ServiceRetrieveModelSerializer
    permission_classes = (IsProvider,)

    def get_queryset(self):
        return Service.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.owner != user:
            raise PermissionDenied("You do not have permission to delete this service.")

        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": f"Service '{instance.name}' successfully marked as deleted."},
            status=status.HTTP_200_OK
        )


@extend_schema(tags=['Service'])
class ServiceRetrieveAPIView(RetrieveAPIView):
    serializer_class = ServiceRetrieveModelSerializer
    queryset = Service.objects.all()
    authentication_classes = ()

    def retrieve(self, request, *args, **kwargs):
        service = get_object_or_404(
            Service.objects.prefetch_related("schedules", "bookings"),
            pk=self.kwargs["pk"]
        )
        serializer = self.get_serializer(service)
        data = serializer.data

        duration = service.duration
        capacity = service.capacity

        weekdays_data = []
        schedules = service.schedules.all()

        for schedule in schedules:
            weekday_name = schedule.weekday
            start_time = schedule.start_time
            end_time = schedule.end_time

            free_slots = []

            current_time = datetime.combine(timezone.now().date(), start_time)
            end_datetime = datetime.combine(timezone.now().date(), end_time)

            while current_time + duration <= end_datetime:
                slot_start = current_time.time()
                slot_end = (current_time + duration).time()

                overlapping_bookings = Booking.objects.filter(
                    service=service,
                    weekday=weekday_name,
                )

                total_booked = 0

                for booking in overlapping_bookings:
                    booking_end = (
                            datetime.combine(timezone.now().date(), booking.start_time)
                            + booking.duration
                    ).time()

                    if booking.start_time < slot_end and booking_end > slot_start:
                        total_booked += booking.seats

                available_capacity = capacity - total_booked

                if available_capacity > 0:
                    free_slots.append({
                        "time": f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}",
                        "available_capacity": available_capacity
                    })

                current_time += duration

            weekdays_data.append({
                "weekday": weekday_name,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
                "free_time": free_slots
            })

        data["weekday"] = weekdays_data

        return Response(data)


@extend_schema(tags=['Booking'])
class BookingCreateAPIView(CreateAPIView):
    serializer_class = BookingModelSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Booking'])
class UserBookingHistoryListAPIView(FilterSearchMixin, ListAPIView):
    serializer_class = BookingHistorySerializer
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticated]

    pagination_class = CustomLimitOffsetPagination
    filterset_fields = 'created_at',
    search_fields = 'service__name', 'weekday', 'start_time', 'seats'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)