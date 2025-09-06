import uuid

from django.db import models # noqa
from django.db.models.base import Model
from django.db.models.fields import UUIDField, DateTimeField


# Create your models here.


class UUIDModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class CreatedBaseModel(UUIDModel):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

