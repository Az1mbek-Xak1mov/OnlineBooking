from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from authen.models import User
from authen.serializers import UserRegistrationSerializer, VerifyOtpSerializer, UserCreateSerializer
from authen.services.otp_service import OtpService
from authen.utils import generate_code


@extend_schema(tags=['Authentication'])
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


@extend_schema(tags=['Authentication'])
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

        otp_service.delete_temp_data(phone)

        return Response(UserCreateSerializer(user).data, status=status.HTTP_200_OK)
