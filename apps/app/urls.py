from app.views import (BookingCreateAPIView, ServiceCategoryListAPIView,
                       ServiceListCreateAPIView, ServiceRetrieveAPIView,
                       UserBookingHistoryListAPIView)
from django.urls import path

urlpatterns = [
    path("bookings/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("services/", ServiceListCreateAPIView.as_view(), name="booking-create"),
    # path("services/", ServiceViewSet.as_view(actions={'get':'list','post':'create'}), name="booking-create"),

    path("services/<uuid:pk>", ServiceRetrieveAPIView.as_view(), name="service-detail"),
    path("category/services/", ServiceCategoryListAPIView.as_view(), name="service-category-list"),
    path("users/booking/hostory/", UserBookingHistoryListAPIView.as_view(), name="user-booking-history"),
]
