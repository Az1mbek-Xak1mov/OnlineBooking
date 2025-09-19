from django.urls import path

from authentication.views import (CustomTokenObtainPairView, CustomTokenRefreshView,
                                  RegisterApiView, VerifyPhoneNumberAPIView, GetMeView)

urlpatterns = [
    path('registration/', RegisterApiView.as_view(), name='register'),
    path('registration/verify/phone_number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'), # TODO id ham qaytsin

    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'), # TODO data kalit ichida user malumotlari qaytsin
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('get-me/', GetMeView.as_view(), name='get-me'),
    # TODO get-me user oziga tegishli bolgan malumotlarni olish
]

