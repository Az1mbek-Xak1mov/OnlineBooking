from django.urls import path
from authen.views import RegisterApiView, VerifyPhoneNumberAPIView, LoginOtpAPIView, VerifyOtpLoginAPIView, \
    CustomTokenObtainPairView, CustomTokenRefreshView

urlpatterns = [
    path('registration/', RegisterApiView.as_view(), name='register'),
    path('registration/verify/phone_number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'),

    path('login/phone_number', LoginOtpAPIView.as_view(), name='login_by_phone_number'),
    path('login/verify/phone_number', VerifyOtpLoginAPIView.as_view(), name='login_verify_by_phone_number'),

    path('login/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
