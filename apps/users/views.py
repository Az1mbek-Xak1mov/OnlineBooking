from service.permissions import IsAdmin, IsModerator
from users.models import RoleChange, User
from users.serializers import (CustomTokenObtainPairSerializer,
                               MyRequestsModelSerializer,
                               RoleChangeModelSerializer,
                               UserCreateSerializer,
                               UserModelSerializer,
                               UserRegistrationSerializer,
                               VerifyOtpSerializer)
from users.utils import OtpService, generate_code
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)
from shared.paginations import CustomLimitOffsetPagination
from django.views.generic import TemplateView


@extend_schema(tags=['Auth'])
class RegisterApiView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        otp_service = OtpService()

        success, ttl = otp_service.save_user_temp(phone_number, serializer.validated_data)
        if not success:
            return Response(
                {"detail": f"Try again after {ttl} seconds."},
                status=status.HTTP_400_BAD_REQUEST
            )

        code = generate_code()
        print(code)
        otp_service.send_otp(phone_number, code, purpose="register")

        return Response(
            {"detail": "OTP code sent."},
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=['Auth'])
class VerifyPhoneNumberAPIView(CreateAPIView):
    serializer_class = VerifyOtpSerializer
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        otp_service = OtpService()
        valid, user_data = otp_service.verify_otp(phone, otp_code, purpose='register')
        print("DEBUG verify result:", valid, user_data)

        if not valid or not user_data:
            return Response({"detail": "Invalid OTP code."}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        otp_service.delete_otp(phone)

        return Response(UserCreateSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(tags=['Auth'])
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['Auth'])
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(tags=['Auth'], responses={200: UserModelSerializer})
class GetMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserModelSerializer(request.user)
        return Response(serializer.data)


@extend_schema(tags=['Auth'], responses={200: RoleChangeModelSerializer})
class RoleChangeCrateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoleChangeModelSerializer


@extend_schema(tags=['Auth'], responses={200: MyRequestsModelSerializer})
class MyRequestsListAPIView(ListAPIView):
    queryset = RoleChange.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = MyRequestsModelSerializer

    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = 'created_at',
    search_fields = 'message',

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)


@extend_schema(tags=['User'], responses={200: UserModelSerializer})
class UserUpdateDeleteGetApiView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=['User'], responses={200: UserModelSerializer})
class UsersListApiView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [IsModerator, IsAdmin]


class UserCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        total = User.objects.count()
        return Response({"count": total})
