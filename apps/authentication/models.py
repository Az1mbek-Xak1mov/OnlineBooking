from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField, TextChoices, BigIntegerField

from shared.manager import CustomUserManager
from shared.models import UUIDBaseModel


class User(AbstractUser, UUIDBaseModel):
    class Type(TextChoices):
        CUSTOMER = 'customer', 'Customer'
        PROVIDER = 'provider', 'Provider'
        ADMIN = 'admin', 'Admin'
        MODERATOR = 'moderator', 'Moderator'

    username = None
    phone_number = CharField(max_length=20, unique=True)
    email = EmailField(blank=True, null=True, unique=False)
    type = CharField(choices=Type.choices, max_length=15, default=Type.CUSTOMER)
    telegram_id = BigIntegerField(unique=True, blank=True, null=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    @property
    def fullname(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"

    @property
    def is_provider(self):
        return self.type == self.Type.PROVIDER  # TODO style

    @property
    def is_admin(self):
        return self.type == 'admin'

    @property
    def is_moderator(self):
        return self.type == 'moderator'

    @property
    def is_customer(self):
        return self.type == 'customer'
