import uuid

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models import CharField, EmailField
from django.db.models.enums import TextChoices
from django.db.models.fields import UUIDField

# Create your models here.


class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user_object(self, phone_number, email, password, **extra_fields):
        if not phone_number:
            raise ValueError("The given phone number must be set")
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.password = make_password(password)
        return user

    def _create_user(self, phone_number, email, password, **extra_fields):
        user = self._create_user_object(phone_number, email, password, **extra_fields)
        user.save(using=self._db)
        return user

    async def _acreate_user(self, phone_number, email, password, **extra_fields):
        user = self._create_user_object(phone_number, email, password, **extra_fields)
        await user.asave(using=self._db)
        return user

    def create_user(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, email, password, **extra_fields)

    create_user.alters_data = True

    async def acreate_user(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return await self._acreate_user(phone_number, email, password, **extra_fields)

    acreate_user.alters_data = True

    def create_superuser(self, phone_number, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, email, password, **extra_fields)

    create_superuser.alters_data = True

    async def acreate_superuser(
            self, phone_number, email=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return await self._acreate_user(phone_number, email, password, **extra_fields)

    acreate_superuser.alters_data = True


class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4())

    class RoleType(TextChoices):
        CUSTOMER = 'customer', 'Customer'
        PROVIDER = 'provider', 'Provider'
        ADMIN = 'admin', 'Admin'
        MODERATOR = 'moderator', 'Moderator'

    username = None
    phone_number = CharField(max_length=20, unique=True)
    email = EmailField(blank=True, null=True, unique=False)
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()
    role = CharField(choices=RoleType.choices)

    @property
    def fullname(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"
