from django.contrib import admin
from django.contrib.admin import ModelAdmin

from authen.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(ModelAdmin):
    pass