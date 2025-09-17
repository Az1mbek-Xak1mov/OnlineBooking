import re
from random import randint  # noqa

from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer, Serializer

from authentication.models import User


class UserRegistrationSerializer(ModelSerializer):
    confirm_password = CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('phone_number', 'password', 'confirm_password', 'first_name', 'last_name')

    def validate_phone_number(self, value):
        clean_phone_number = re.sub(r"\D", "", value)

        if not clean_phone_number.startswith("998"):
            raise ValidationError("Phone number must start with '998'")

        if not clean_phone_number.isdigit():
            raise ValidationError("Phone number must be digits, example: 998 000 00 00")

        if len(clean_phone_number) != 12:
            raise ValidationError("Phone number must be 12 digits, example: 998 00 000 00 00")

        if User.objects.filter(phone_number=clean_phone_number).exists():
            raise ValidationError("This phone number is already registered.Go Login in!")

        return clean_phone_number

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise ValidationError({'Confirm Password': "Passwords do not match."})
        attrs.pop('confirm_password', None)

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        # user = User(**validated_data)
        # user.set_password(password)
        # user.save()
        return user


class UserCreateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "phone_number", "password", "first_name", "last_name"
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VerifyOtpSerializer(Serializer):
    phone_number = CharField(max_length=12)
    otp_code = CharField(max_length=6)

    def validate_phone_number(self, value):
        clean_phone_number = re.sub(r"\D", "", value)

        if not clean_phone_number.isdigit():
            raise ValidationError("Phone number must be digits, example: 998 000 00 00")

        if len(clean_phone_number) != 12:
            raise ValidationError("Phone number must be 12 digits, example: 998 00 000 00 00")

        return clean_phone_number
