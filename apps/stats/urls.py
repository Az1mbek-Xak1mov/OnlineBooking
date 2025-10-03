from django.urls import path
from stats.views import UserCountAPIView, ServiceCountAPIView, ServiceLocationsAPIView

urlpatterns = [
    path("users/count/", UserCountAPIView.as_view(), name="user-count"),
    path("service/count/", ServiceCountAPIView.as_view(), name="user-count"),
    path('locations-with-service/', ServiceLocationsAPIView.as_view(), name='locations-with-service'),
]