from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db.transaction import atomic
from django.shortcuts import render  # noqa
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from app.models import Service, Booking
from app.permissions import IsProvider
from app.serializers import ServiceSerializer, BookingSerializer


class ServiceViewSet(ModelViewSet):
    queryset = Service.objects.all().select_related("owner", "category")
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProvider]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(owner=user)

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
                service=service, weekday=date_obj, start_time=start_time
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