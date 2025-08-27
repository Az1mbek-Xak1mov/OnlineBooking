from random import randint

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from authen.models import User

class UserSerializer(ModelSerializer):
    confirm_password = CharField(write_only=True)
    class Meta:
        model = User
        fields = ('email' , 'password','confirm_password', 'first_name' ,'last_name')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("This email is already registered.Go Login in!")
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise ValidationError({'Confirm Password': "Passwords do not match."})
        attrs.pop('confirm_password', None)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user