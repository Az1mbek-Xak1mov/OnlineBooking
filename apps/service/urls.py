from service.views import (BookingCreateAPIView, MyServicesListApiView,
                           PendingBookingListAPIView, ServiceCategoryListAPIView,
                           ServiceDeleteUpdateGetAPIView, ServiceListCreateAPIView,
                           UserBookingHistoryListAPIView, ServiceImageListCreateAPIView, ServiceImageDestroyAPIView)
from django.urls import path

urlpatterns = [
    path("category/services/", ServiceCategoryListAPIView.as_view(), name="service-category-list"),

    path("services/", ServiceListCreateAPIView.as_view(), name="service-create"),
    path("services/<uuid:pk>/", ServiceDeleteUpdateGetAPIView.as_view(), name="service-detail"),
    path("services/my-services/", MyServicesListApiView.as_view(), name="my-services-list"),

    path("bookings/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("users/booking/pending/", PendingBookingListAPIView.as_view(), name="users-booking-history-pending"),
    path("users/booking/history/", UserBookingHistoryListAPIView.as_view(), name="users-booking-history"),

    path("services/<uuid:pk>/images/", ServiceImageListCreateAPIView.as_view()),
    path("services/<uuid:service_pk>/images/<uuid:image_pk>/", ServiceImageDestroyAPIView.as_view(), name="service-image-destroy"),
]
