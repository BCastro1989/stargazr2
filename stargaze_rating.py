#!/usr/bin/python
# -*- coding: UTF-8 -*-
import debug
import json
import math
import os
import pprint
import requests
import time as t

from datetime import datetime as dt
from flask import Flask

from helpers import (
    get_current_unix_time,
    convert_YMDHMS_to_unix
)

import apis as apis

SECONDS_IN_DAY = 86400

def get_darkness_times(lat_selected, lng_selected, time):
    """Get times of day's darkness start/stop as unix time

    args: String representing lat/lng coords
    returns: Int of 10-digit Unix Time (integer seconds)
    """
    sunset_data = apis.sunrise_sunset_time(lat_selected, lng_selected, time)

    # start of astronomical twilight is good enough to begin stargazing
    # Nautical Twilight End = Start of Astronomical Twilight and vice-versa
    morning_stagazing_ends = sunset_data['results']['nautical_twilight_begin']
    night_stagazing_begins = sunset_data['results']['nautical_twilight_end']

    morning_stagazing_ends_unix = convert_YMDHMS_to_unix(morning_stagazing_ends)
    night_stagazing_begins_unix = convert_YMDHMS_to_unix(night_stagazing_begins)

    # Midnight Sun, never dark
    if morning_stagazing_ends_unix == 1 or morning_stagazing_ends_unix == 1:
        return {'sun_status': 'Midnight Sun'}
    # Polar Night, always dark
    if morning_stagazing_ends_unix == 0 or night_stagazing_begins_unix == 0:
        return {'sun_status': 'Polar Night'}

    # Approximations of times following days. Looses accuracy at very high latitudes near equinox
    # Needed for TZ offsets since API always uses UTC, the times returned may be wrong day
    prevday_stagazing_begin_unix = night_stagazing_begins_unix - SECONDS_IN_DAY
    nxtday_stagazing_ends_unix = morning_stagazing_ends_unix + SECONDS_IN_DAY
    nxtday_stagazing_begin_unix = night_stagazing_begins_unix + SECONDS_IN_DAY

    darkness_times = {
        'sun_status': 'Normal',
        'prev_day_dusk': prevday_stagazing_begin_unix,
        'curr_day_dawn': morning_stagazing_ends_unix,
        'curr_day_dusk': night_stagazing_begins_unix,
        'next_day_dawn': nxtday_stagazing_ends_unix,
        'next_day_dusk': nxtday_stagazing_begin_unix
    }

    return darkness_times


def set_time_to_dark(darkness_times, curr_time_unix):
    """Sets Time for requests to once it is dark

    Checks if it is currently dark enough for stargazing,
    if not, sets time to once it is dark. darkness times
    are for the start/end of astronomical twilight.
    This can be used to infer roughly what time the sun is
    far enough below horizon to allow stargazing

    args: Unix times for current time, darkness start/end time
    returns: Boolean
    """
    # Must consider several cases because sunrise-sunset API processes all times as UTC, such that
    # depending on the time zone of user, the darkness times returned may be given for the following day.
    # This might be fixed by using user time zone from location, or passing TZ from client
    if curr_time_unix <= darkness_times["prev_day_dusk"]:
        return darkness_times['prev_day_dusk']  # if before sunset, adjust time to after
    elif curr_time_unix <= darkness_times['curr_day_dawn']:
        return curr_time_unix  # After Sunset, Before Sunrise
    elif curr_time_unix <= darkness_times['curr_day_dusk']:
        return darkness_times['curr_day_dusk']  # if before sunset, adjust time to after
    elif curr_time_unix <= darkness_times['next_day_dawn']:
        return curr_time_unix  # After Sunset, Before Sunrise
    elif curr_time_unix <= darkness_times['next_day_dusk']:
        return darkness_times['next_day_dusk']
    else:
        raise Exception("set_time_to_dark: Time selected outside bounds")


def get_weather_at_time(lat_selected, lng_selected, time=None):
    """Gets Weather report for location and time specified.

    args: lat/lng and time for stargazing site
    returns: dictionary with just the weather data we're interested in
    """
    # TODO: ONLY get data we need from API requests? Would be faster but requires
    # a lot more params in url request used. Probably worth it in the long run
    weather_data = apis.dark_sky(lat_selected, lng_selected, time)

    # NOTE Hourly forcast data is only availible for next 48 hours
    # If more than 48 hours ahead, only have daily weather, so just assume it applies at night

    # TODO The response from weather_data is slightly different if looking at future weather report!
    # Test responses at various future times, verify that below keys still exist and get correct values
    precip_prob = weather_data['currently']['precipProbability']
    humidity = weather_data['currently']['humidity']
    visibility = weather_data['currently']['visibility']
    cloud_cover = weather_data['currently']['cloudCover']
    moon_phase = weather_data['daily']['data'][0]['moonPhase']  # 0 tells to grab todays phase. allows 0-7 for phases over next week

    return {
        'precipProb': precip_prob,
        'humidity': humidity,
        'visibility': visibility,
        'cloudCover': cloud_cover,
        'moonPhase': moon_phase,
    }


def get_driving_distance(lat_origin, lng_origin, lat_selected, lng_selected):
    """Gets approx driving distance and trip time to the given coordinates.

    args: lat/lng for origin and stargazing site selcted
    returns: dictionary with distance in time and space, in km and human readable
    """

    dist_data = apis.gmaps_distance(lat_origin, lng_origin, lat_selected, lng_selected)

    if 'duration' in dist_data['rows'][0]['elements'][0]:
        duration_text = dist_data['rows'][0]['elements'][0]['duration']['text']
        duration_value = dist_data['rows'][0]['elements'][0]['duration']['value']
        distance_text = dist_data['rows'][0]['elements'][0]['distance']['text']
        distance_value = dist_data['rows'][0]['elements'][0]['distance']['value']
    else:
        duration_text = 'N/A'
        duration_value = 'N/A'
        distance_text = 'N/A'
        distance_value = 'N/A'

    driving_distance = {
        'duration_text': duration_text,
        'duration_value': duration_value,
        'distance_text': distance_text,
        'distance_value': distance_value,
    }

    return driving_distance


def get_site_elevation(lat, lng):
    """Gets the elevation at the given coordinates.

    args: lat/lng for stargazing site selcted
    returns: dictionary with elevation, distance in meters
    """
    elev_data = apis.gmaps_elevation(lat, lng)
    return elev_data['results'][0]['elevation']


def site_rating_desciption(site_quality):
    """Describe the site based off it's rating.

    args: Site quality 0-100
    returns: String describing site quality
    """
    if site_quality > 95:
        site_quality_discript = "Excellent"
    elif site_quality > 90:
        site_quality_discript = "Very Good"
    elif site_quality > 80:
        site_quality_discript = "Good"
    elif site_quality > 50:
        site_quality_discript = "Fair"
    elif site_quality > 30:
        site_quality_discript = "Poor"
    elif site_quality >= 0:
        site_quality_discript = "Terrible"
    else:
        site_quality_discript = "Could Not Determine Stargazing Quality. Weather or Light Pollution Data unavailible"
    return site_quality_discript


def calculate_rating(precipProbability, humidity, cloudCover, lightPol):
    """ Calculate the stargazing quality based off weather, light pollution, etc.

    args: site statistics, light pollution
    returns: Double rating from 0 - 100, -1 for err
    """
    # TODO Equation for calulcating the rating needs some work.
    # 7 percent cloud cover and otherwise perfect conditions should not be a rating of 77, Fair.

    # TODO This can also factor in "elevation" and "visibility" but currently does not

    # Rate quality based on each parameter
    precip_quality = (1 - math.sqrt(precipProbability))
    humid_quality = (math.pow(-humidity + 1, (1/3)))
    cloud_quality = (1 - math.sqrt(cloudCover))
    if isinstance(lightPol, float):
        # should give rating between 0.9995 (Middle of Nowhere) - 0.0646 (Downtown LA)
        lightpol_quality = (abs(50 - lightPol) / 50)
    else:
        return -1

    # Find overall site quality using weighted average
    site_quality_rating = ((((precip_quality * lightpol_quality * cloud_quality) * 8) + (humid_quality * 2)) / 10) * 100

    return site_quality_rating


# TODO: CleanUp/Refactor
def get_stargaze_report(lat_org, lng_org, lat_selected, lng_selected, stargazing_time=None):
    """get stargazing report based on given coordinates.

    args:
    lat_org/lng_org: gps coords of origin (user location) as float
    lat_selected/lng_selected: gps coords of selected stargazing site as float
    time: in unix int

    returns: dictionary with data needed for API response/display in front end
    """
    curr_time = get_current_unix_time()

    if not stargazing_time:
        stargazing_time = curr_time

    # Disallow requests for stargazing more than 8 days in future
    if stargazing_time > curr_time + SECONDS_IN_DAY * 8:
        return {'status': "Reports are only availible for the next week"}

    # Determine what times it gets dark on a given day, if it is not dark at requested stargazing time, set time to once it gets dark
    # Account for 24+ hr long days and nights in the arctice and anarctice
    darkness_times = get_darkness_times(lat_selected, lng_selected, stargazing_time)
    if darkness_times['sun_status'] == 'Midnight Sun':
        return {'status': "One cannot stargaze in the land of the midnight sun. Try going closer to the equator!"}
    elif darkness_times['sun_status'] == 'Polar Night':
        stargazing_time = curr_time
    else:
        # TODO User-facing message that time was changed to ___ (w/ TZ adjust!)
        stargazing_time = set_time_to_dark(darkness_times, stargazing_time)

    weather_data = get_weather_at_time(lat_selected, lng_selected, stargazing_time)

    precip_prob = weather_data['precipProb']
    humidity = weather_data['humidity']
    cloud_cover = weather_data['cloudCover']
    lunar_phase = weather_data['moonPhase']
    elevation = get_site_elevation(lat_selected, lng_selected)
    light_pol = apis.light_pollution(float(lat_selected), float(lng_selected))
    driving_distance = get_driving_distance(lat_org, lng_org, lat_selected, lng_selected)
    site_quality = calculate_rating(precip_prob, humidity, cloud_cover, light_pol)
    site_quality_discript = site_rating_desciption(site_quality)

    # Only get CDS chart if requested time is within 24 hours
    if stargazing_time < curr_time + SECONDS_IN_DAY:
        cds_chart = apis.nearest_csc(float(lat_selected), float(lng_selected))
    else:
        cds_chart = None

    site_data = {
        'status': "Success!",
        'siteQuality': site_quality,
        'siteQualityDiscript': site_quality_discript,
        'precipProb': precip_prob,
        'humidity': humidity,
        'cloudCover': cloud_cover,
        'lightPol': light_pol,
        'elevation': elevation,
        'lunarphase': lunar_phase,
        'CDSChart': cds_chart
    }
    site_data.update(driving_distance)

    return json.dumps(site_data)


def test():
    time = get_current_unix_time()

    # Test stargazing using San Francisco as user location, Pt Reyes at stargazing site, no time param
    result = get_stargaze_report(37.7360512, -122.4997348, 38.116947, -122.925357)
    print("********** SF-Pt. Reyes TEST w/o time **********")
    print(result, "\n")

    # Test stargazing using San Francisco as user location, Stony Gorge at stargazing site, time is in 12 hr
    result = get_stargaze_report(37.7360512, -122.4997348, 39.580110, -122.524105, time + SECONDS_IN_DAY/2)
    print("********** SF-Stony Gorge w/ time **********")
    print(result, "\n")

    # Test stargazing using San Francisco as user location, Pt Reyes at stargazing site, time is in 24 hr
    result = get_stargaze_report(37.7360512, -122.4997348, 38.116947, -122.925357, time + SECONDS_IN_DAY)
    print("********** SF-Pt. Reyes w/ time **********")
    print(result, "\n")

    # Test stargazing using San Francisco as user location, Stony Gorge at stargazing site, time is in 36 hr
    result = get_stargaze_report(37.7360512, -122.4997348, 39.580110, -122.524105, time + SECONDS_IN_DAY*1.5)
    print("********** SF-Stony Gorge w/ time **********")
    print(result, "\n")




if __name__ == "__main__":
    test()
