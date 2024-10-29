import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from Happyface4 import utilities

logger = logging.getLogger("getData")


class Command(BaseCommand):
    help = "Command that goes through the different installed Analyses and calls their respective getData functions."

    def add_arguments(self, parser):
        analyses_configs = utilities.get_Analyses_from_apps(apps)
        analysis_names = [a.name for a in analyses_configs] + ["all"]
        parser.add_argument(
            "analyses",
            nargs="*",
            choices=analysis_names,
            default="all",
            help="Analyses for which to call getData (optional, default all)",
        )

    def handle(self, *args, **options):
        analyses_configs = [
            analysis
            for analysis in utilities.get_Analyses_from_apps(apps)
            if options["analyses"] == "all" or (analysis.name in options["analyses"])
        ]
        # to speed things up, the different getData calls are multithreaded where max_workers specify the number of threads which should be used
        with ThreadPoolExecutor(max_workers=len(analyses_configs)) as executer:
            for config in analyses_configs:
                # submit another function call to the multithreading executer
                future = executer.submit(self.getDataRoutine, config)

    def getDataRoutine(self, analysis):
        # callable for multithreading
        for instance in analysis.instances:
            now = timezone.now()
            minutes = now.hour * 60 + now.minute
            get_data_every = instance.get("get_data_every", 1)
            pull_intervall_minutes = settings.PULL_INTERVAL.seconds // 60
            # skip if it is not time to get data for this instance (based on the pull interval and the get_data_every parameter in the instance config)
            if (
                minutes % (pull_intervall_minutes * get_data_every)
                >= pull_intervall_minutes
            ):
                logger.debug(f"SKIP: {instance['name']} (of module: ){analysis.name})")
                continue

            logger.debug(
                f"Start get data for module: {analysis.name}, instance: {instance['name']}"
            )
            try:
                analysis.getData(instance)
                logger.info(
                    f"Fetched data for module: {analysis.name}, instance: {instance['name']}"
                )

            except Exception as e:
                logger.error(
                    f"""
#################################################
An Error has occurred in the getData function.
Analysis:       {analysis.name}
Instance:       {instance["name"]}
Verbose name:   {instance["verbose_name"]}
Error:
{traceback.format_exc(limit=10)}
"""
                )
