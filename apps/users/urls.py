from django.urls import path
from users.views import (CustomTokenObtainPairView, CustomTokenRefreshView,
                         GetMeView, MyRequestsListAPIView, RegisterApiView,
                         RoleChangeCrateAPIView, UsersListApiView,
                         UserUpdateDeleteGetApiView, VerifyPhoneNumberAPIView, VerifyPhoneAndSetPasswordAPIView,
                         ConfirmPhoneNumberApiView)

urlpatterns = [
    path('registration/', RegisterApiView.as_view(), name='register'),
    path('registration/verify/phone_number/', VerifyPhoneNumberAPIView.as_view(), name='verify_phone_number'),

    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('get-me/', GetMeView.as_view(), name='get-me'),

    path('role-change-request/', RoleChangeCrateAPIView.as_view(), name='role-change'),
    path('my-requests/', MyRequestsListAPIView.as_view(), name='my-requests'),
    path("users/<uuid:pk>", UserUpdateDeleteGetApiView.as_view(), name="user-detail"),
    path("users/", UsersListApiView.as_view(), name="users"),
    path('registration/update_passwod/' , VerifyPhoneAndSetPasswordAPIView.as_view(), name='forgot-password'),
    path('registration/forgot_password/' , ConfirmPhoneNumberApiView.as_view(), name='forgot-password'),

]
