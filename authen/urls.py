from django.urls import path
from authen.views import RegisterApiView, VerifyPhoneNumberAPIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('registration/', RegisterApiView.as_view(), name='register'),
    path('verify/phone_number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
