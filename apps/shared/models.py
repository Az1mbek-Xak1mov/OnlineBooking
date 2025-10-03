from django.db.models import Func, Model
from django.db.models.fields import DateTimeField, UUIDField


class GenRandomUUID(Func):
    function = "gen_random_uuid"
    template = "%(function)s()"
    output_field = UUIDField()


class UUIDBaseModel(Model):
    id = UUIDField(primary_key=True, db_default=GenRandomUUID(), editable=False)

    class Meta:
        abstract = True
        required_db_vendor = 'postgresql'


class CreatedBaseModel(UUIDBaseModel):
    updated_at = DateTimeField(auto_now=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


print(1)