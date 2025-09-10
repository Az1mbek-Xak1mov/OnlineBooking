from django.urls import path

from authen.views import (CustomTokenObtainPairView, CustomTokenRefreshView,
                          RegisterApiView, VerifyPhoneNumberAPIView)

urlpatterns = [
    path('registration/', RegisterApiView.as_view(), name='register'),
    path('registration/verify/phone_number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'),

    path('login/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
