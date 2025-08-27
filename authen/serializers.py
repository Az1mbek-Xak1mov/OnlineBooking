from random import randint

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from authen.models import User

def generate_code() -> int:
    return randint(100000, 999999)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('email' , 'password')

    def validate(self, attrs):
        print(attrs)