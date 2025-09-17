from django.urls import path

from app.views import BookingCreateAPIView, ServiceViewSet, ServiceRetrieveAPIView, ServiceCategoryListAPIView, \
    UserBookingHistoryListAPIView

urlpatterns = [
    path("api/bookings/", BookingCreateAPIView.as_view(), name="booking-create"),
    path("api/services/", ServiceViewSet.as_view(actions={'get':'list','post':'create'}), name="booking-create"),

    path("api/services/<uuid:pk>", ServiceRetrieveAPIView.as_view(), name="service-detail"),
    path("api/category/services/", ServiceCategoryListAPIView.as_view(), name="service-category-list"),
    path("api/user/booking/hostory", UserBookingHistoryListAPIView.as_view(), name="user-booking-history"),
]
