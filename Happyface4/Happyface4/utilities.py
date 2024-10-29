import copy
import datetime
import logging

from django.conf import settings
from django.utils import timezone

from .forms import DateTimeForm
from .status import STATUS


logger = logging.getLogger("Happyface4")


class DummyInstanceStatus(object):
    """
    Helper object that can be used to propagate a single instance status to the template.
    This is generally only used for the statuses info(-1) and technical issue(-2).
    :param time: The timestamp for this status. Normally just the time of the request.
    :type time: datetime.datetime
    :param status: The status in form of a number between -2 and 2.
    :type status: int
    """

    def __init__(self, time, status):
        self.time = time
        self.status = status
        self.itered = False

    def __len__(self):
        # Only one status
        return 1

    def __iter__(self):
        # little hack to make this object iterable so that it returns itself
        # in only one iteration
        return [self].__iter__()

    def latest(self, _):
        # To imitate the latest method of an QuerySet. As this object only represent one
        # status it returns itself.
        return self

    def last(self):
        # To imitate the `last` method of a QuerySet. As this object only represent one
        # status it returns itself.
        return self


class CategoryNav(object):
    def __init__(self, name, instance):
        self.name = name
        self.instances = [instance]

    def latest_status(self):
        return max([i.latest_status() for i in self.instances])

    def statuses_list(self):
        cat_status_list = []
        # find instance with most status entries
        most_status_entries = copy.deepcopy(
            max([inst.status for inst in self.instances], key=len)
        )

        # find the worst status at each time
        for timepoint in most_status_entries:
            instance_status_list = []
            for inst in self.instances:
                if type(inst.status) is not DummyInstanceStatus:
                    timediffs = [
                        abs(timepoint.time - status.time) for status in inst.status
                    ]
                    nearest_status_index = timediffs.index(min(timediffs))
                    nearest_status = inst.status[nearest_status_index]
                    if type(nearest_status) is int:
                        instance_status_list.append(nearest_status)
                    else:
                        instance_status_list.append(nearest_status.status)
                else:
                    instance_status_list.append(inst.status.status)
            cat_status_list.append(
                {"time": timepoint.time, "status": max(instance_status_list)}
            )
        return cat_status_list


class InstanceNav(object):
    def __init__(self, name, verbose_name, status, order=-1):
        self.status = status
        self.verbose_name = verbose_name
        self.name = name
        self.order = order

    def latest_status(self):
        # returns the newest status
        return self.status.latest("time").status


def extract_time_from_request(request):
    if request.method == "GET":
        form = DateTimeForm(request.GET)
        if request.GET.get("reload") == "true":
            now = timezone.localtime(timezone.now())
            form = DateTimeForm(
                {"time": now.time().isoformat(timespec="minutes"), "date": now.date()}
            )
            return None, now, form, True
        elif form.is_valid():
            data_cleaned = form.cleaned_data
            date_localized = timezone.make_aware(
                datetime.datetime.combine(data_cleaned["date"], data_cleaned["time"])
            )
            return date_localized, date_localized, form, False

    now = timezone.localtime(timezone.now())
    form = DateTimeForm(
        {"time": now.time().isoformat(timespec="minutes"), "date": now.date()}
    )
    return None, now, form, False


def get_Analyses_from_apps(apps):
    filtered_apps = []
    for app in apps.get_app_configs():
        if app.path.startswith(settings.ANALYSES_DIR):
            filtered_apps.append(app)
    return filtered_apps


def get_apps_with_instances_in_category(app_config_list, category):
    """
    creates a list of all apps with their respective instances that are in the category

    another filtering step that is used to determine which analyses to call with what arguments
    to get all the divs in the category

        :param app_config_list: list of configuration objects of the Analyses.
        :param category: the name of the category in which the analyses have registered an instance
        :type app_config_list: list of Subclasses to the django.apps.AppConfig class
        :type category: string
        :returns: all apps that have an instance in the category.
        :rtype: list of tuples of the AppConfig subclass of an Analysis with instances
        in the category along with a list of the instances of the corresponding class.

    .. note: The categories returns the class as well as the entire configuration dict of that particular instance.
    """
    apps_in_category = []
    for app_config in app_config_list:
        instances_in_category = []
        for instance in app_config.instances:
            if instance["category"] == category:
                instances_in_category.append(instance)
        if len(instances_in_category) != 0:
            apps_in_category.append((app_config, instances_in_category))
    return apps_in_category


def render_instances(analyses_list, category, time, request):
    divs = []
    instance_orders = []
    ananlyses_to_render = get_apps_with_instances_in_category(analyses_list, category)
    # catch case where the category string doesn't match the category of any analysis
    if not ananlyses_to_render:
        return []
    for app_config, instances_list in ananlyses_to_render:
        # the instance is a tuple where the first item is the app config and the second is a list of all
        # instances of the app that have to be rendered
        for instance in instances_list:
            anaDiv = app_config.builddiv(time, instance, request)
            divs.append(anaDiv)
            instance_orders.append(instance.get("order", -1))

    # show analyses with negative/unspecified ordering specifications last
    instance_orders = [len(instance_orders) if o < 0 else o for o in instance_orders]

    # order analyses according to ordering specifications
    sorted_orders, sorted_divs = zip(*sorted(zip(instance_orders, divs)))
    return sorted_divs


def get_statuses_of_instances(app_list, time, time_range):
    """
    generates a list of nav_elements from a list of analyses
    """
    from .models import InstanceStatus

    categories_list = []

    for app in app_list:
        for instance in app.instances:
            name = instance["name"]
            verbose_name = instance["verbose_name"]
            cat = instance["category"]
            order = instance.get("order", -1)
            if instance.get("is_info", False):
                instance_status = DummyInstanceStatus(time=time, status=STATUS.INFO)
            else:
                try:
                    instance_status = app.get_instance_status(
                        instance=instance, time=time, time_range=time_range
                    )
                except:
                    logger.error(
                        f"No 'get_instance_status' method implemented or 'is_info' flag set for instance {name}."
                    )
                    instance_status = DummyInstanceStatus(
                        time=time, status=STATUS.TECHNICAL_ISSUE
                    )
            instance_object = InstanceNav(
                name=name,
                verbose_name=verbose_name,
                status=instance_status,
                order=order,
            )
            # check if category of current instance already exists in the categories list
            if cat not in [n.name for n in categories_list]:
                # if not create a new Category object and pass it the current instance
                # object
                categories_list.append(CategoryNav(name=cat, instance=instance_object))
            else:
                # if the category object already exists append the instance object to the
                # instances list
                for c in categories_list:
                    if c.name == cat:
                        c.instances.append(instance_object)
    # sort the array
    categories_list.sort(key=lambda cat: cat.name.lower())
    for cat in categories_list:
        # order instances as specified in config
        cat.instances.sort(
            key=lambda ins: len(cat.instances) if ins.order < 0 else ins.order
        )
    return categories_list
