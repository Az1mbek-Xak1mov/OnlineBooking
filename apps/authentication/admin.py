from authentication.models import (AdminUserProxyUser, CustomerProxyUser,
                                   ModeratorProxyUser, ProviderProxyUser,
                                   RoleChange, User)
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.forms import HiddenInput


class UserModelAdminMixin(admin.ModelAdmin):
    list_display = "phone_number", "email", "first_name", "last_name", "is_active"
    search_fields = "phone_number", "email", "first_name", "last_name"
    _type = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self._type is not None:
            return qs.filter(type=self._type)
        return qs

    def save_model(self, request, obj, form, change):
        if self._type is not None:
            obj.type = self._type

        raw_password = getattr(obj, "password", None)
        if raw_password and not raw_password.startswith("pbkdf2_"):
            obj.password = make_password(raw_password)

        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'type' in form.base_fields and self._type is not None:
            form.base_fields['type'].initial = self._type
            form.base_fields['type'].widget = HiddenInput()
        return form


@admin.register(CustomerProxyUser)
class CustomerAdmin(UserModelAdminMixin):
    _type = User.Type.CUSTOMER


@admin.register(ProviderProxyUser)
class ProviderAdmin(UserModelAdminMixin):
    _type = User.Type.PROVIDER


@admin.register(AdminUserProxyUser)
class AdminUserModelAdmin(UserModelAdminMixin):
    _type = User.Type.ADMIN


@admin.register(ModeratorProxyUser)
class ModeratorAdmin(UserModelAdminMixin):
    _type = User.Type.MODERATOR


@admin.register(RoleChange)
class RoleChangeAdmin(admin.ModelAdmin):
    list_display = ("user", "short_message", "is_read", "is_accepted", "created_at")
    list_filter = ("is_read", "is_accepted", "created_at")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name", "message")
    ordering = ("is_read", "-created_at")
    actions = ["mark_as_read", "accept_requests"]

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj and not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=["is_read"])
        return obj

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    @admin.action(description="Mark selected requests as read")
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f"{count} request(s) marked as read ✅")

    @admin.action(description="Accept selected requests and set role = Provider")
    def accept_requests(self, request, queryset):
        for r in queryset.filter(is_accepted__isnull=True):
            r.is_accepted, r.is_read = True, True
            r.save(update_fields=["is_accepted", "is_read"])

            if r.user.type != User.Type.PROVIDER:
                r.user.type = User.Type.PROVIDER
                r.user.save(update_fields=["type"])
        self.message_user(request, "Selected requests accepted")

    def short_message(self, obj):
        return f"{obj.message[:30]}..." if len(obj.message) > 30 else obj.message

    short_message.short_description = "Message"
