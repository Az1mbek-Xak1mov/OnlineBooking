from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProvider(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "type", None) == "provider")
