import uuid
from django.db import models
from django.utils import timezone


class BaseManager(models.Manager):
    """
    Manager for BaseModel that filters out soft-deleted records.

    Methods:
        get_queryset: Returns a queryset that excludes soft-deleted records.
    """

    def get_queryset(self):
        """
        Returns a queryset that excludes records with a non-null deleted_at field.

        Returns:
            QuerySet: The queryset excluding soft-deleted records.
        """
        return super().get_queryset().filter(deleted_at=None)


class BaseModel(models.Model):
    """
    Base model that includes UUID primary key, created, updated, and soft-deleted timestamps.

    Managers:
        objects (BaseManager): Manager that excludes soft-deleted records.
        admin_objects (Manager): Default manager that includes all records.
    """

    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = BaseManager()
    admin_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Soft deletes the record by setting the deleted_at field to the current time.
        """
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """
        Restores a soft-deleted record by setting the deleted_at field to None.
        """
        self.deleted_at = None
        self.save()
