from app.views import (BookingCreateAPIView, ServiceCategoryListAPIView,
                       ServiceListCreateAPIView, ServiceRetrieveAPIView,
                       UserBookingHistoryListAPIView, ServiceDeleteAPIView, MyServicesListApiView,
                       PendingBookingListAPIView)
from django.urls import path

urlpatterns = [
    path("category/services/", ServiceCategoryListAPIView.as_view(), name="service-category-list"),

    path("services/", ServiceListCreateAPIView.as_view(), name="service-create"),
    path("services/delete/<uuid:pk>", ServiceDeleteAPIView.as_view(), name="service-delete"),
    path("services/detail/<uuid:pk>", ServiceRetrieveAPIView.as_view(), name="service-detail"),
    path("services/my-services/", MyServicesListApiView.as_view(), name="my-service"),

    path("bookings/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("users/booking/history/pending/", PendingBookingListAPIView.as_view(), name="user-booking-history-pending"),
    path("users/booking/history/", UserBookingHistoryListAPIView.as_view(), name="user-booking-history"),
]
