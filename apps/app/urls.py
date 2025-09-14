from django.urls import path

from app.views import BookingCreateAPIView, ServiceViewSet

urlpatterns = [
    path("api/bookings/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("api/services/", ServiceViewSet.as_view(actions={'get':'list','post':'create'}), name="booking-create"),
]
