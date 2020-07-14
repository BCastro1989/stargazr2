import os
import requests

from helpers import (
    convertUnixToYMDFormat
)


from light_pollution import getLightPollution
from nearest_csc import nearest_csc

DARKSKY_API_KEY = os.environ.get('DARKSKY_API_KEY', '')
G_MAPS_API_KEY = os.environ.get('G_MAPS_API_KEY', '')

SUNSET_URL = "https://api.sunrise-sunset.org/json"
DARKSKY_URL = "https://api.darksky.net/forecast/%s/%.4f,%.4f,%d"
GMAPS_ELEV_URL = "https://maps.googleapis.com/maps/api/elevation/json"
GMAPS_DIST_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

def dark_sky_api(lat_selected, lon_selected, time):
    """Gets Weather report for location and time specified using darksky api

    args: lat/lon and time for stargazing site
    returns: weather api response in json format
    """
    if not DARKSKY_API_KEY:
        raise Exception("Missing API Key for DarkSky")
    
    request = requests.get(DARKSKY_URL %(DARKSKY_API_KEY, lat_selected, lon_selected, time))
    return request.json()


def gmaps_elevation_api(lat_selected, lon_selected):
    if not G_MAPS_API_KEY:
        raise Exception("Missing API Key for Google Maps")

    elev_params ={
        "locations": str(lat_selected)+","+str(lon_selected),
        "key": G_MAPS_API_KEY
    }

    elev_request = requests.get(GMAPS_ELEV_URL, params=elev_params)
    return elev_request.json()


def gmaps_distance_api(lat_origin, lon_origin, lat_selected, lon_selected):
    if not G_MAPS_API_KEY:
        raise Exception("Missing API Key for Google Maps")

    dist_params ={
        "units": "imperial", # use metric outside USA?
        "origins": str(lat_origin)+","+str(lon_origin),
        "destinations": str(lat_selected)+","+str(lon_selected),
        "key": G_MAPS_API_KEY
    }

    dist_request = requests.get(GMAPS_DIST_URL, params=dist_params)

    return dist_request.json()

    
def sunrise_sunset_time_api(lat_selected, lon_selected, time):
    params = {
        "lat": lat_selected,
        "lng": lon_selected,
        "formatted": 0,
        "date": str(convertUnixToYMDFormat(time)) if time else "",
    }

    # TODO: Currently only returns darkness times for today, must work for next 48 hours
    # API accepts date paramter but in YYYY-MM-DD format, not unix time
    request = requests.get(SUNSET_URL, params=params)
    return request.json()


def light_pollution_api(lat_starsite, lon_starsite):
    return getLightPollution(float(lat_starsite),float(lon_starsite))


def nearest_csc_api(lat_starsite,lon_starsite):
    return nearest_csc(float(lat_starsite),float(lon_starsite))