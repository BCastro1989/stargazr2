
from datetime import datetime as dt
import time as t

def getCurrentUnixTime():
    """Get current time in UNIX format.

    args: none
    returns: Integer of 10-digit Unix Time (integer seconds)
    """
    return int(t.time())


def convertUnixToYMDFormat(unixtime):
    """Convert time from unix epoch to Human Readable YYYY-MM-DD

    args: int representing unix time
    returns: String representing time in YYYY-MM-DD
    """
    return dt.utcfromtimestamp(unixtime).strftime("%Y-%m-%d")

