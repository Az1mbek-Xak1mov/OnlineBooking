from django.db.models import Manager, QuerySet


class ServiceQuerySet(QuerySet):
    def active(self):
        return self.filter(is_deleted=False)

    def delete(self):
        return self.update(is_deleted=True)


class ServiceManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super().get_queryset()
