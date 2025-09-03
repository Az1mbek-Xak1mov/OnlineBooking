from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from authen.models import User
from authen.serializers import UserSerializer, ListUserSerializer


class RegisterApiView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserListApiView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = ListUserSerializer
    permission_classes = [IsAuthenticated]