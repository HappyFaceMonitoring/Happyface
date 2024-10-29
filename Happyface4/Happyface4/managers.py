import logging
from datetime import timedelta

from django.conf import settings

# from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .status import STATUS
from .utilities import DummyInstanceStatus

logger = logging.getLogger(__name__)


class InstanceStatusManager(models.Manager):
    def update_or_create(self, time, instance, category, status):
        from . import models as m

        ins, created = m.Instance.objects.get_or_create(name=instance)
        cat, created = m.Category.objects.get_or_create(name=category)
        super().update_or_create(
            time=time, instance=ins, category=cat, defaults={"status": status}
        )

    def get_instance_status(self, time, instance_name, category, time_range):
        from . import models as m

        # add a small buffer to the time_range to make sure that the time_range is inclusive
        time_range += timedelta(minutes=1)
        try:
            ins = m.Instance.objects.get(name=instance_name)
            cat = m.Category.objects.get(name=category)
            status_list = (
                self.filter(instance=ins, category=cat)
                .filter(time__gt=time - time_range)
                .filter(time__lte=time)
                .order_by("time")
            )
            # check if the QurySet contains any result
            if status_list.exists():
                return status_list
            else:
                raise ObjectDoesNotExist

        # The ObjectDoesNotExist Error can come from the QuerySet operation because some
        # instance or category entry is missing or from the  if-else-statement because the
        # QuerySet is empty
        except ObjectDoesNotExist:
            logger.warning(
                f"No instance status for instance {instance_name} in the database (category: {category}, time: {time - time_range} to {time})"
            )
            status_interval = DummyInstanceStatus(
                time=time, status=STATUS.TECHNICAL_ISSUE
            )
        return status_interval
