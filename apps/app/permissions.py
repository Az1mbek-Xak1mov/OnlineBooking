from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProvider(BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user and user.is_authenticated and user.is_provider
