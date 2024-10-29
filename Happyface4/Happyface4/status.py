from typing import final


@final
class STATUS(object):
    """A small object to access the numeric codes of the different statuses."""

    TECHNICAL_ISSUE = -2
    INFO = -1
    OK = 0
    WARNING = 1
    CRITICAL = 2
