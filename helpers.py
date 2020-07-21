
from datetime import datetime as dt
import time as t


def get_current_unix_time():
    """Get current time in UNIX format.

    args: none
    returns: Integer of 10-digit Unix Time (integer seconds)
    """
    return int(t.time())


def convert_unix_to_YMD(unixtime):
    """Convert time from unix epoch to Human Readable YYYY-MM-DD

    args: int representing unix time
    returns: String representing time in YYYY-MM-DD
    """
    return dt.utcfromtimestamp(unixtime).strftime("%Y-%m-%d")


def convert_YMDHMS_to_unix(timestamp):
    """Convert time to unix epoch from human-readable YYYY-MM-DD-H-M-S.
    Assumes time is UTC, no time zones or DLS

    args: String representing time in YYYY-MM-DD
    returns: int representing unix time
    """
    timestamp = dt.strptime(timestamp[:-6], '%Y-%m-%dT%H:%M:%S')
    return int((timestamp - dt(1970, 1, 1)).total_seconds())
