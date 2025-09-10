from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import User


class Customer(User):
    class Meta:
        proxy = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


class Provider(User):
    class Meta:
        proxy = True
        verbose_name = "Provider"
        verbose_name_plural = "Providers"


class AdminUser(User):
    class Meta:
        proxy = True
        verbose_name = "Admin"
        verbose_name_plural = "Admins"


class Moderator(User):
    class Meta:
        proxy = True
        verbose_name = "Moderator"
        verbose_name_plural = "Moderators"


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ("phone_number", "email", "first_name", "last_name", "is_active")
    search_fields = ("phone_number", "email", "first_name", "last_name")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=User.RoleType.CUSTOMER)


@admin.register(Provider)
class ProviderAdmin(ModelAdmin):
    list_display = ("phone_number", "email", "first_name", "last_name", "is_active")
    search_fields = ("phone_number", "email", "first_name", "last_name")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=User.RoleType.PROVIDER)


@admin.register(AdminUser)
class AdminUserAdmin(ModelAdmin):
    list_display = ("phone_number", "email", "first_name", "last_name", "is_active")
    search_fields = ("phone_number", "email", "first_name", "last_name")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=User.RoleType.ADMIN)


@admin.register(Moderator)
class ModeratorAdmin(ModelAdmin):
    list_display = ("phone_number", "email", "first_name", "last_name", "is_active")
    search_fields = ("phone_number", "email", "first_name", "last_name")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=User.RoleType.MODERATOR)
