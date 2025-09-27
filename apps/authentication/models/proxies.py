from authentication.models.users import User


class CustomerProxyUser(User):
    class Meta:
        proxy = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


class ProviderProxyUser(User):
    class Meta:
        proxy = True
        verbose_name = "Provider"
        verbose_name_plural = "Providers"


class AdminUserProxyUser(User):
    class Meta:
        proxy = True
        verbose_name = "Admin"
        verbose_name_plural = "Admins"


class ModeratorProxyUser(User):
    class Meta:
        proxy = True
        verbose_name = "Moderator"
        verbose_name_plural = "Moderators"
