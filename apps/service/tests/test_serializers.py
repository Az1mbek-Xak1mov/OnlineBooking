import pytest
from rest_framework.exceptions import ValidationError
from users.models import RoleChange, User
from users.serializers import (CustomTokenObtainPairSerializer,
                               MyRequestsModelSerializer,
                               RoleChangeModelSerializer, UserCreateSerializer,
                               UserModelSerializer, UserRegistrationSerializer,
                               VerifyOtpSerializer)


@pytest.mark.django_db
class TestUserRegistrationSerializer:

    @pytest.fixture
    def user_data(self):
        return {
            "phone_number": "998123456789",
            "password": "test123",
            "confirm_password": "test123",
            "first_name": "John",
            "last_name": "Doe"
        }

    def test_validate_phone_number_success(self, user_data):
        serializer = UserRegistrationSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["phone_number"] == "998123456789"

    def test_validate_phone_number_invalid_prefix(self, user_data):
        user_data["phone_number"] = "997123456789"
        serializer = UserRegistrationSerializer(data=user_data)
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate_password_mismatch(self, user_data):
        user_data["confirm_password"] = "wrong"
        serializer = UserRegistrationSerializer(data=user_data)
        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid(raise_exception=True)
        assert "Confirm Password" in exc_info.value.detail

    def test_create_user(self, user_data):
        serializer = UserRegistrationSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert isinstance(user, User)
        assert user.phone_number == "998123456789"


@pytest.mark.django_db
class TestUserCreateSerializer:

    @pytest.fixture
    def user_data(self):
        return {
            "phone_number": "998987654321",
            "password": "test123",
            "first_name": "Alice",
            "last_name": "Smith"
        }

    def test_create_user_sets_password(self, user_data):
        serializer = UserCreateSerializer(data=user_data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        assert user.check_password("test123")
        assert user.first_name == "Alice"


@pytest.mark.django_db
class TestVerifyOtpSerializer:

    def test_validate_phone_number_success(self):
        serializer = VerifyOtpSerializer(data={"phone_number": "998123456789", "otp_code": "123456"})
        serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["phone_number"] == "998123456789"

    def test_validate_phone_number_invalid(self):
        serializer = VerifyOtpSerializer(data={"phone_number": "12345", "otp_code": "123456"})
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998101010101", password="test123")

    def test_validate_returns_users_info(self, user):
        serializer = CustomTokenObtainPairSerializer(data={"phone_number": user.phone_number, "password": "test123"})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        assert "users" in data
        assert data["users"]["phone_number"] == user.phone_number


@pytest.mark.django_db
class TestUserModelSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998202020202", password="test123", first_name="Bob",
                                        last_name="Lee")

    def test_serialization(self, user):
        serializer = UserModelSerializer(user)
        data = serializer.data
        assert data["phone_number"] == user.phone_number
        assert data["first_name"] == "Bob"


@pytest.mark.django_db
class TestRoleChangeModelSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998303030303", password="test123")

    @pytest.fixture
    def role_change_data(self):
        return {"message": "Upgrade me"}

    def test_create_role_change(self, user, role_change_data):
        serializer = RoleChangeModelSerializer(data=role_change_data,
                                               context={"request": type("Request", (), {"user": user})()})
        serializer.is_valid(raise_exception=True)
        role_change = serializer.save()
        assert role_change.user == user
        assert role_change.message == "Upgrade me"
        assert role_change.is_read is False
        assert role_change.is_accepted is None


@pytest.mark.django_db
class TestMyRequestsModelSerializer:

    @pytest.fixture
    def user(self):
        return User.objects.create_user(phone_number="998404040404", password="test123")

    @pytest.fixture
    def role_change(self, user):
        return RoleChange.objects.create(user=user, message="Request 1")

    def test_serialization(self, role_change):
        serializer = MyRequestsModelSerializer(role_change)
        data = serializer.data
        assert data["message"] == "Request 1"
        assert data["user"] == role_change.user.id


print(1)