from authentication.views import (CustomTokenObtainPairView,
                                  CustomTokenRefreshView, GetMeView,
                                  MyRequestsListAPIView, RegisterApiView,
                                  RoleChangeCrateAPIView,
                                  VerifyPhoneNumberAPIView)
from django.urls import path

urlpatterns = [
    path('registration/', RegisterApiView.as_view(), name='register'),
    path('registration/verify/phone_number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'),

    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('get-me/', GetMeView.as_view(), name='get-me'),

    path('role-change-request/', RoleChangeCrateAPIView.as_view(), name='role-change'),
    path('my-requests/', MyRequestsListAPIView.as_view(), name='my-requests'),
]
