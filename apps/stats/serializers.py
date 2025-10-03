from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from service.models import Location


class LocationWithServiceSerializer(ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'lat', 'lng', 'service_name')
