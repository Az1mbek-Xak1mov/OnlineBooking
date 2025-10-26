from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from service.models import Service, Location
from stats.serializers import LocationWithServiceSerializer
from users.models import User


@extend_schema(tags=['Stats'])
class UserCountAPIView(APIView):
    serializer_class = None  # Add explicit serializer_class for schema generation
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        total = User.objects.count()
        return Response({"count": total})


@extend_schema(tags=['Stats'])
class ServiceCountAPIView(APIView):
    serializer_class = None  # Add explicit serializer_class for schema generation
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        total = Service.objects.count()
        return Response({"count": total})


@extend_schema(tags=['Stats'])
class ServiceLocationsAPIView(APIView):
    serializer_class = None  # Add explicit serializer_class for schema generation
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        qs = Location.objects.select_related('service').all()
        serializer = LocationWithServiceSerializer(qs, many=True)
        return Response(serializer.data)

