from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import logging
from django.core.management import call_command
import signal
import time
from threading import Event
import requests

logger = logging.getLogger("getData")


class Command(BaseCommand):
    help = "Command that goes through the different installed Analyses and calls their respective getData functions. This is repeated every timestep (set in the settings.py).\nIf this task shall run in the background you can use >>nohup ./manage.py getDataRoutine &<<."

    def __init__(self, *args, **kwargs):
        self.exit = Event()
        signal.signal(signal.SIGINT, self.__handler)
        super().__init__(*args, **kwargs)

    def __handler(self, sig, frame):
        logger.info("received SIGINT, stops fetching new Data.")
        self.exit.set()

    def handle(self, *args, **options):
        sleep_sec = getattr(
            settings, "GETDATA_SLEEP", 60
        )  # time between checks if it's time to fetch data in seconds.
        while not self.exit.is_set():
            if time.time() % settings.PULL_INTERVAL.seconds <= sleep_sec:
                # send healthcheck signal start
                self.ping_healthcheck("/start")
                # execute getData
                call_command("getData")
                # send healthcheck signal
                self.ping_healthcheck()
            self.exit.wait(sleep_sec)
        self.exit.clear()

    def ping_healthcheck(self, url_appendix=""):
        """Send a signal to healthcheck.io to monitor happyface automatically

        Args:
            url_appendix (str, optional): appendix to the healthchecks.io url, can be used measure the time of the getData command with "\\start". Defaults to "".
        """
        if (
            not settings.DEBUG
            and hasattr(settings, "HEALTHCHECK_PING_URL")
            and settings.HEALTHCHECK_PING_URL
        ):
            try:
                requests.get(settings.HEALTHCHECK_PING_URL + url_appendix, timeout=10)
            except requests.RequestException as e:
                logger.error("Healthcheck Ping failed: %s" % e)
