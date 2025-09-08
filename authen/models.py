from django.contrib.auth.models import AbstractUser
from django.db.models import EmailField, Model, TextChoices, CharField, Func
from django.db.models.fields import UUIDField

from authen.customs import CustomUserManager


class GenRandomUUID(Func):
    """
    Represents the PostgreSQL gen_random_uuid() function.
    """
    function = "gen_random_uuid"
    template = "%(function)s()"  # no args
    output_field = UUIDField()


class UUIDBaseModel(Model):
    id = UUIDField(primary_key=True, db_default=GenRandomUUID(), editable=False)

    class Meta:
        abstract = True
        required_db_vendor = 'postgresql'


class User(AbstractUser, UUIDBaseModel):
    class Type(TextChoices):
        CUSTOMER = 'customer', 'Customer'
        PROVIDER = 'provider', 'Provider'
        ADMIN = 'admin', 'Admin'
        MODERATOR = 'moderator', 'Moderator'

    username = None
    phone_number = CharField(max_length=20, unique=True)
    email = EmailField(blank=True, null=True, unique=False)
    type = CharField(choices=Type.choices, max_length=15)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    @property
    def fullname(self):
        return f"{self.first_name.capitalize()} {self.last_name.capitalize()}"

    @property
    def is_customer(self):
        return self.type == 'customer'

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
