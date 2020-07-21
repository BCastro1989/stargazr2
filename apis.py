import os
import requests

from helpers import (
    convert_unix_to_YMD,
)


from light_pollution import get_light_pollution
from nearest_csc import get_nearest_csc

DARKSKY_API_KEY = os.environ.get('DARKSKY_API_KEY', '')
G_MAPS_API_KEY = os.environ.get('G_MAPS_API_KEY', '')

SUNSET_URL = "https://api.sunrise-sunset.org/json"
DARKSKY_URL = "https://api.darksky.net/forecast/%s/%.4f,%.4f,%d"
GMAPS_ELEV_URL = "https://maps.googleapis.com/maps/api/elevation/json"
GMAPS_DIST_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def dark_sky(lat_selected, lng_selected, time):
    """Gets Weather report for location and time specified using darksky api

    args: lat/lng and time for stargazing site
    returns: weather api response in json format
    """
    if not DARKSKY_API_KEY:
        raise Exception("Missing API Key for DarkSky")

    request = requests.get(DARKSKY_URL % (DARKSKY_API_KEY, lat_selected, lng_selected, time))
    return request.json()


def gmaps_elevation(lat_selected, lng_selected):
    """Gets the elevation at given coordinates.

    args: lat/lng for stargazing site selcted
    returns: json response with elevation data in meters
    """
    if not G_MAPS_API_KEY:
        raise Exception("Missing API Key for Google Maps")

    elev_params = {
        'locations': str(lat_selected)+","+str(lng_selected),
        'key': G_MAPS_API_KEY
    }

    elev_request = requests.get(GMAPS_ELEV_URL, params=elev_params)
    return elev_request.json()


def gmaps_distance(lat_origin, lng_origin, lat_selected, lng_selected):
    """Gets the distance between two sets of coords

    args: lat/lng for origin and stargazing site selcted
    returns: json response with driving distance (meters) and time (seconds)
    """

    if not G_MAPS_API_KEY:
        raise Exception("Missing API Key for Google Maps")

    dist_params = {
        'origins': str(lat_origin)+","+str(lng_origin),
        'destinations': str(lat_selected)+","+str(lng_selected),
        'key': G_MAPS_API_KEY
    }

    dist_request = requests.get(GMAPS_DIST_URL, params=dist_params)

    return dist_request.json()


def sunrise_sunset_time(lat_selected, lng_selected, time):
    """Gets the times the sun will rise/set, and reach "twilight" conditions sufficent for stargazing

    args: lat/lng for stargazing site selcted
    returns: json response with driving distance (meters) and time (seconds)
    """
    params = {
        'lat': lat_selected,
        'lng': lng_selected,
        'formatted': 0,
        'date': str(convert_unix_to_YMD(time)) if time else "",
    }

    # TODO: Currently only returns darkness times for today, must work for next 48 hours
    # API accepts date paramter but in YYYY-MM-DD format, not unix time
    request = requests.get(SUNSET_URL, params=params)
    return request.json()


def light_pollution(lat_selected, lng_selected):
    """Determines Light Pollution Levels. Internal API.

    args: lat/lng for stargazing site selcted
    returns: json response with light pollution levels (additional brightness ratio)
    """
    return get_light_pollution(float(lat_selected), float(lng_selected))


def nearest_csc(lat_selected, lng_selected):
    """Gets nearest Clear Sky Chart. Internal API.

    args: lat/lng for stargazing site selcted
    returns: json response with the nearest CSC.
    """
    return get_nearest_csc(float(lat_selected), float(lng_selected))
