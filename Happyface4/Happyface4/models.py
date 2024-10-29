from django.db import models
from . import managers


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")


class Instance(models.Model):
    name = models.CharField(max_length=100, verbose_name="Analysis Name")


class InstanceStatus(models.Model):
    """:class:`~models.Model` to save the status of the instances in the db."""

    objects = managers.InstanceStatusManager()
    time = models.DateTimeField("Time of the status")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        (-2, "technical issue"),  # a technical issue within Happyface ocurred
        (-1, "info"),  # e.g. it doesn't make sense to provide an status
        (0, "ok"),  # everything is fine and works as expected
        (1, "warning"),  # the analysis data goes over the warning threshold
        (2, "critical"),  # the analysis data goes over the critical threshold
    ]
    status = models.SmallIntegerField(
        "status of the instance (-2, 'technical issue'), \
        (-1, 'info'), (0, 'ok'), (1, 'warning'), (2, 'critical')",
        choices=STATUS_CHOICES,
    )
