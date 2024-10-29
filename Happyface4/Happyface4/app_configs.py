import logging
from abc import ABCMeta, abstractmethod
from asyncio.log import logger
from typing import Final, final

from django.apps import AppConfig
from django.conf import settings
from django.template import loader
from django.utils import timezone

from .status import STATUS

# TODO: Make each instance one Analysis Config instance and not some list of dictionaries


class AnalysisConfig(AppConfig, metaclass=ABCMeta):
    """
    Abstract class handling the common methods of a Analysis and representing all of the analysis
    configurations.
    """

    logger: Final[logging.Logger] = logging.getLogger("Happyface4")
    """
    :meta private:
    The logger which can be used to log to. E.g. with ``self.logger.error("..msg..")``.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        standard name of the analysis is the module name, which is the name of the folder in
        which the analysis is laying
        """

        pass

    @property
    @abstractmethod
    def instances(self) -> list:
        """
        :class:`List <list>` of :class:`dicts <dict>` which contain the info and settings of
        the different instances of one Analysis.
            Should have at least the following contents:

            .. code-block:: python

                instances = [
                    {
                    # Name of the analysis instance
                    "name": "happyface4_analysis_instance_1",
                    # This will get the visible header of the analysis
                    "verbose_name": "Happyface 4 Analysis Example 1",
                    # Category of the instance. Each category is displayed in a sepereate
                    # site.
                    "category": "Batch System",
                    # Url to data source
                    "source": "example.com",
                    # A short description of the instance
                    "description": "Status of the Compute Element Tests",
                    # If the instance doesn't has an internal status to set and has only
                    # the status `info`, this flag can be set to True.
                    # In this case the `get_instance_status()` method doesn't need to be
                    # specified and `save_data_to_db()` should return `None,None`.
                    "is_info": True,
                    # A threshold for the 'critical' and the 'warning' alert level. Putting
                    # it here is useful if there are different threshold for different
                    # instances in an analysis.
                    "critical_thresholds": 0.8,
                    "warning_thresholds": 0.5,
                    # The file for the HTML template.
                    "template": "happyface4_analysis/happyface4_analysis.html",
                    # The time interval in which the data is fetched. This is a int giving multiples of settings.PULL_INTERVAL
                    get_data_every: 1,
                    }
                ]
        """

        pass

    def __init__(self, app_name, app_module):
        # calls the __init__ function of the parent class AppConfig
        super().__init__(app_name, app_module)

        # replaces all whitespaces with underscores and makes all lowercase for the names
        # of the analysis and the instances
        self.name = self.name.replace(" ", "_").lower()

        # check if instances dicts are complete and if not insert some standard values
        for i, inst in enumerate(self.instances):
            if not inst.get("name"):
                inst["name"] = self.name + "_" + str(i)
            else:
                # replace whitespaces and make all lowercase
                inst["name"] = inst["name"].replace(" ", "_").lower()
            if not inst.get("verbose_name"):
                inst["verbose_name"] = inst["name"].replace("_", " ").capitalize()
            if not inst.get("category"):
                inst["category"] = "Uncategorized"
            if not inst.get("dt"):
                inst["dt"] = settings.PULL_INTERVAL
            if not inst.get("source"):
                self.logger.error(
                    "The source variable is missing for analysis {} instance {}.".format(
                        self.name, inst["name"]
                    )
                )
                raise NotImplementedError(
                    "The source variable is missing for analysis {} instance {}.".format(
                        self.name, inst["name"]
                    )
                )
            if not inst.get("description"):
                inst["description"] = "There is no description available yet."
                self.logger.warning(
                    "The description for {}. {} ist missing.".format(
                        self.name, inst["name"]
                    )
                )
            # check if template is set, if not use the class variable to deduce the
            # template name
            if not inst.get("template"):
                inst["template"] = "{0}/{0}.html".format(self.name)
            # check if the get_data_every variable is set, if not set it to 1
            if not inst.get("get_data_every"):
                inst["get_data_every"] = 1

    @final
    def getData(self, instance):
        """
        Central function which is called by the global getData command for each instance.
        Handles the process of fetching and saving data and calculating the instance status.

        :meta private:
        :param instance: The dict with the properties of a analysis instance, this is
                overgiven by the global
                :class:`getData <~commands.management.commands.getData.command>` function.
        :type instance: dict

        """

        from .models import InstanceStatus

        data = self.extract_data_from_url(instance)

        # checks whether data was fetched and if not sets the status for the actual time
        if data:
            status, time = self.save_data_to_db(data, instance)
        else:
            status = STATUS.TECHNICAL_ISSUE
            time = timezone.now()
            self.logger.error(f"Instance {instance['name']}: Couldn't fetch data.")
        # Don't save the status if the save_data_to_db method doesn't return a status
        if status is not None:
            # saves the alert level
            InstanceStatus.objects.update_or_create(
                time=time,
                instance=instance["name"],
                category=instance["category"],
                status=status,
            )

    @abstractmethod
    def extract_data_from_url(self, instance):
        """This function uses source given in the instance to fetch the data from the
        source. This function is individual to each source and should therefore be
        overwritten.

        :param instance: The dict with the properties of a analysis instance, this is
                         overgiven automatically by the :func:`getData` function.
        :type instance: dict

        :return: The data fetched from the url.
        :rtype: dict or list of dicts or list

        """

        self.logger.error(
            "The function extract_data_from_url of instance {} doesn't exist.".format(
                instance["name"]
            )
        )

        dictionary = {}
        return dictionary

    @abstractmethod
    def save_data_to_db(self, data, instance):
        """This function takes the fetched data and preperes it for the database and
        finally saves it in the database.
        This function needs to be overwritten!
        The preperation includes removing all data not needed and making all analytical
        calculation needed. The more calculation is done here the less calculation needs
        to be done when a html request comes and therefore the site will load faster.
        But remember this function is called every time the global getData function is
        called (e.g. every 15min) so the the calculations should be too big.

        To save the data to the database (you can define the database tables in the
        ``models.py``) you need to do something like this:

        .. code-block:: python

           from . import models
           models.ExampleModel.objects.create(instance=instance['name'], \
            example_data=prepered_data, ...)

        For more information please look into the
        `django documentation <https://docs.djangoproject.com/en/3.1/ref/models/>`_.

        :param data: This is exactly the data which is returned from the
                     :func:`extract_data_from_url` function.
        :type data: dict or list
        :param instance: The dict with the properties of a analysis instance, this is
                         overgiven automatically by the :func:`getData` function.
        :type instance: dict
        :returns:
            - **instance_status** - The alert level of the whole instance. This is
                important for the display of the alert level in the navigation bar on the
                website. ``-2: 'Technical issue', -1: 'info', 0: 'ok', 1: 'warning',
                2: 'error'``
            - **time** - The time the data is fetched. This can be the actual time, in
                this case :func:`~django.utils.timezone.now` would be the right choice, or
                it can be a time which is recorded in the data itself.
        :rtype: (int, ~datetime.datetime)

        """

        # refresh imports
        from . import models

        self.logger.error(
            "The function save_data_to_db of instance {} doesn't exist.".format(
                instance["name"]
            )
        )
        instance_status = None
        time = None  # timezone.now()
        # prepare the fetched data for the dataset and make all analytical calculations
        # needed
        # only save the data in the db which is really needed

        return instance_status, time

    @final
    def builddiv(self, time_of_readout, instance, request):
        """Central function which is called if there is a http request to a category with
        this instance in it. Calls the retrieve_data_from_db function and renders the
        template with the data optained from the database.

        :meta private:
        :param time_of_readout: The time the data is requested for.
        :type time_of_readout: ~datetime.datetime

        :param instance: The dict with the properties of a analysis instance.
        :type instance: dict

        :param request: A django request instance with all the information needed to send
                        answer the request.
        :type request: ~django.http.HttpRequest

        :returns: The rendered Template which contains the complete and ready HTML code for
                  this analysis.
        :rtype: django Template object

        """

        # loads the global setting of the timedelta after which new data is fetched. So we
        # only need to search for data in the frame time_of_readout-dt to time_of_readout.
        dt = instance["dt"]
        # tries to get the data. If the data returned is None, then this tries the to get
        # the data dt (mins) in the past and iterates this until some data is found or it
        # needs more then 8 iterations.
        # An additional warning gets displayed in this case.
        history_steps = 0
        while history_steps < 8:
            # gets the data for the requested time. The timestep the data was produced can
            # differ from the time in the request. So an additional timestamp is overgiven.
            data, timestamp = self.retrieve_data_from_db(instance, time_of_readout, dt)
            if data and history_steps == 0:
                # gets the status of the data to the requested time from the database.
                # It could also be calculated from the data, but this would need some time
                # and a short response time of the website is more important.
                if instance.get("is_info", False):
                    status = STATUS.INFO
                else:
                    status = (
                        self.get_instance_status(
                            instance=instance, time=time_of_readout
                        )
                        .latest("time")
                        .status
                    )
                break
            elif data and history_steps > 0:
                status = STATUS.WARNING
                break
            else:
                time_of_readout -= dt
                history_steps += 1

        # the context dict which is overgiven to the template
        context = {
            "status": status if data else STATUS.TECHNICAL_ISSUE,
            "old_data_warning": (
                {
                    "hours": (history_steps * dt).seconds // 3600,
                    "min": ((history_steps * dt).seconds // 60) % 60,
                }
                if history_steps and data
                else None
            ),
            "data": data,
            "instance": instance,
            "timestamp": timestamp,
            "analysis_name": self.name,
            "data_sources": (
                instance["source"]
                if type(instance["source"]) == list
                else [instance["source"]]
            ),
        }
        # Load and render the template with the context dict.
        template = loader.get_template(instance["template"])
        return template.render(context, request)

    @abstractmethod
    def retrieve_data_from_db(self, instance, time_of_readout, dt):
        """This function is responsible for loading the data of this instance from the
        database for the desired time.
        The filtering of the database for the desired time can be defined in the
        ``managers.py`` file, so this function only needs to check if data is available at
        that time.
        Then the data must be returned together with the timestamp. The timestamp shows
        when the data is from.
        This function is empty and needs to be overwritten.

        :param instance: The dict with the properties of a analysis instance the data was
                        requested for.
        :type instance: dict

        :param time_of_readout: The date and time the data was requested for.
        :type time_of_readout: ~datetime.datetime

        :param dt: Specifies the time range in which to search for data. So that for data
                   between time_of_readout - dt and time_of_readout must be searched.
        :type dt: ~datetime.timedelta

        :returns:
            - **data** - A dict or
                :class:`Django Queryset <django.db.models.query.QuerySet>` with the data.
                This is directly loaded in the template and has to be prepared for it.
            - **timestamp** - The date and time the data is from.
        :rtype: (dict or ~django.db.models.query.QuerySet, ~datetime.datetime)

        """
        from . import models

        self.logger.error(
            "The function retrieve_data_from_db of instance {} doesn't exist.".format(
                instance["name"]
            )
        )

        data = None
        timestamp = None
        return data, timestamp

    def get_instance_status(self, instance, time, time_range=None):
        """This function gets or calculates the status of a instance.
        This function is empty and needs to be overwritten.

        :param instance: The dict with the properties of a analysis instance the instance
                         status was requested for.
        :type instance: dict

        :param time: The time in which the data was retrieved for which the
                                instance status is requested.
        :type time: ~datetime.datetime

        :param time_range: Specifies the time range in which to search for data statuses.
                   So that for data between time - time_range and time must
                   be searched.
        :type time_range: ~datetime.timedelta

        :returns: A QuerySet that contains Objects with ``status`` and ``time`` attributes
                  (e.g. InstanceStatus objects or a utilities.DummyInstanceStatus object)
        :rtype: QuerySet or DummyInstanceStatus
        """
        from .models import InstanceStatus

        if not time_range or time_range <= settings.PULL_INTERVAL:
            time_range = settings.PULL_INTERVAL * instance.get("get_data_every", 1)

        return InstanceStatus.objects.get_instance_status(
            time=time,
            instance_name=instance["name"],
            category=instance["category"],
            time_range=time_range,
        )
