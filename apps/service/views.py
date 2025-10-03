from datetime import datetime, timezone

from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from service.mixins import FilterSearchMixin
from service.models import Booking, Service, ServiceCategory
from service.permissions import IsProvider
from service.serializers import (BookingHistorySerializer, BookingModelSerializer,
                                 ServiceCategoryModelSerializer,
                                 ServiceModelSerializer,
                                 ServiceUpdateModelSerializer)
from django.db.models.aggregates import Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView,
                                     get_object_or_404)
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
    permission_classes = IsProvider,IsAuthenticated

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


@extend_schema(tags=["Service"])
class ServiceDeleteUpdateGetAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceUpdateModelSerializer
    permission_classes = (IsProvider,)

    def get_queryset(self):
        # only non-deleted services
        return Service.objects.filter(is_deleted=False)

    def get_object(self):
        # centralize lookup + ownership check
        qs = self.get_queryset().prefetch_related("schedules", "bookings")
        obj = get_object_or_404(qs, pk=self.kwargs["pk"])

        # check ownership
        if obj.owner_id != self.request.user.id:
            # Option A: raise PermissionDenied (403)
            raise PermissionDenied("You do not have permission to access this service.")
            # Option B (preferred in some APIs for privacy): raise Http404()
            # from django.http import Http404
            # raise Http404

        return obj

    def retrieve(self, request, *args, **kwargs):
        service = self.get_object()
        serializer = self.get_serializer(service)
        data = serializer.data

        duration = service.duration
        capacity = service.capacity

        weekdays_data = []

        for schedule in service.schedules.all():
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
                    start_time__lt=slot_end,
                    end_time__gt=slot_start
                )

                total_booked = overlapping_bookings.aggregate(total=Sum("seats"))["total"] or 0
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

    def perform_update(self, serializer):
        # ensure owner before saving (get_object() will raise if not owner)
        instance = self.get_object()
        # if you want an explicit check:
        if instance.owner_id != self.request.user.id:
            raise PermissionDenied("You do not have permission to update this service.")
        serializer.save()

    def perform_destroy(self, instance):
        # ensure owner before deleting (delete() calls get_object() so this is extra-safe)
        if instance.owner_id != self.request.user.id:
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



@extend_schema(tags=['Booking'])
class BookingCreateAPIView(CreateAPIView):
    serializer_class = BookingModelSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['Booking'])
class PendingBookingListAPIView(ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingModelSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return Booking.objects.none()
        return qs.filter(status=Booking.StatusType.PENDING, user=self.request.user)


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
