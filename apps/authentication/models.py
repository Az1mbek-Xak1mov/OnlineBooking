from django.contrib.auth.models import AbstractUser
from django.db.models import (CASCADE, BigIntegerField, BooleanField,
                              CharField, EmailField, ForeignKey, TextChoices,
                              TextField)
from shared.manager import CustomUserManager
from shared.models import CreatedBaseModel, UUIDBaseModel


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
        return self.type == self.Type.PROVIDER

    @property
    def is_admin(self):
        return self.type == self.Type.ADMIN

    @property
    def is_moderator(self):
        return self.type == self.Type.MODERATOR

    @property
    def is_customer(self):
        return self.type == self.Type.CUSTOMER


class RoleChange(UUIDBaseModel, CreatedBaseModel):
    user = ForeignKey('authentication.User', CASCADE, related_name='role_change_requests', editable=False)
    message = TextField(editable=False)
    is_read = BooleanField(default=False, editable=False)
    is_accepted = BooleanField(null=True, blank=True,
                               help_text='If you accept, the users role will be changed from Customer to Provider')

    class Meta:
        verbose_name = 'Change Role Request'
        verbose_name_plural = 'Change Role Requests'
        ordering = ['-created_at', '-is_read']
