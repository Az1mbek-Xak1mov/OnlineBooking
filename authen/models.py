import uuid

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, EmailField
from django.db.models.enums import TextChoices
from django.db.models.fields import UUIDField

from authen.customs import CustomUserManager

# Create your models here.


class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)

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
    role = CharField(choices=RoleType.choices, max_length=15)

    @property
    def fullname(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"

# class RoleRequest(Model):
#     id = UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
#     sender = ForeignKey('authen.User', on_delete=CASCADE, related_name='sender_request')
#     receiver = ManyToManyField('authen.User', null=True, blank=True, related_name='receiver_request')
#     message = TextField()
#     is_read = BooleanField(default=False)
#     is_accepted = BooleanField(null=True, blank=True)
#     created_at = DateTimeField(auto_now_add=True)
#
#     class Meta:
#         ordering = 'read_only','-created_at',
