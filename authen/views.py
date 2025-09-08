from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from authen.models import User
from authen.serializers import (PhoneOtpSerializer, UserCreateSerializer,
                                UserRegistrationSerializer,
                                VerifyOtpSerializer)
from authen.utils import OtpService, generate_code


@extend_schema(tags=['Auth/Register'])
class RegisterApiView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        phone_number = serializer.validated_data['phone_number']
        otp_service = OtpService()

        success, ttl = otp_service.save_user_temp(phone_number, serializer.validated_data)

        if not success:
            raise ValidationError(f"Try again after {ttl} seconds.")

        code = generate_code()
        otp_service.send_otp(phone_number, code)

        return serializer


@extend_schema(tags=['Auth/Register'])
class VerifyPhoneNumberAPIView(CreateAPIView):
    serializer_class = VerifyOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']

        otp_service = OtpService()
        valid, user_data = otp_service.verify_otp(phone, otp_code)

        if not valid or not user_data:
            return Response({"detail": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        otp_service.delete_otp(phone)

        return Response(UserCreateSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth/Login/PhoneNumber'])
class LoginOtpAPIView(CreateAPIView):
    serializer_class = PhoneOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']

        code = generate_code()
        otp_service = OtpService()
        otp_service.send_otp(phone, code)

        return Response({"detail": "OTP code sent."}, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth/Login/PhoneNumber'])
class VerifyOtpLoginAPIView(CreateAPIView):
    serializer_class = PhoneOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data.get('otp_code')

        if not otp_code:
            return Response({"detail": "OTP code is required."}, status=status.HTTP_400_BAD_REQUEST)

        otp_service = OtpService()
        if not otp_service.verify_otp(phone, otp_code):
            return Response({"detail": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(phone_number=phone)

        otp_service.delete_otp(phone)

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": user.id,
            "phone_number": user.phone_number
        }

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth/Login'])
class CustomTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=['Auth/Login'])
class CustomTokenRefreshView(TokenRefreshView):
    pass
