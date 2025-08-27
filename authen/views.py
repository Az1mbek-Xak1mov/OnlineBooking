from rest_framework.generics import CreateAPIView

from authen.models import User
from authen.serializers import UserSerializer


class RegisterApiView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

