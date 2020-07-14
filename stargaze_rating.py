#!/usr/bin/python
# -*- coding: UTF-8 -*-
from datetime import datetime as dt
from flask import Flask

from helpers import (
    getCurrentUnixTime
)

from apis import (
    dark_sky_api,
    gmaps_distance_api,
    gmaps_elevation_api,
    sunrise_sunset_time_api,
    light_pollution_api,
    nearest_csc_api
    )

import debug
import json
import math
import os
import pprint
import requests
import time as t

app = Flask(__name__)
DARKSKY_API_KEY = os.environ.get('DARKSKY_API_KEY', '')
G_MAPS_API_KEY = os.environ.get('G_MAPS_API_KEY', '')

PATH = "csc_data"
FILENAME = "csc_sites.json"
MAX_DIST_KM = 100

# Features this API could use
# P0: [✓] No stargazing reports during the day
# P1: [✓] URL for img of nearest CLEAR SKY Chart, none if > 100 miles, display distance to site + name?
# P2: [✓] Allow user to specify what time to check
# P3: [ ] TIME of Next ISS overpass + visibility, az/alt
# P4: [ ] Any planets visible, where (specific + rough locations - i.e. az/art and general direction and height)
# P4: [ ] Key Meisser Objects, and other popular deep sky objects

# Improvements to Code Quality/Standards
# [ ] Lint/Check for PEP-8
# [ ] Isolate API calls in seperate functions
# [ ] Have 3 API endpoints: Stargazing, Driving Distance, CSC (Later: ISS, Planets, Meisser, etc)

# ToDo Tweaks/Optomize
# [ ] getDarknessTimes
    # P1: [ ] TODO: Currently only returns darkness times for today, must work for next 48 hours
        # API accepts date paramter but in YYYY-MM-DD format, not unix time
    # P2: [ ] TODO: These times may be meaningless above/below (An)arctic Circle.
        # Check what API results are for arctic locations at different times of year
        # If Midnight Sun, tell user no stargazing possible :(
        # If Polar Night, they can stargaze whenever they want! :)
    # P1: [ ] TODO: I just found out the times here dont explicitly account for Daylight Savings.
        # This may or may not be an issue...
# [ ] getWeatherAtTime
    # P3: [ ] TODO: ONLY get data we need from API requests? Would be faster but requires
        # a lot more params in url request used. Probably worth it in the long run
    # P1: [ ] TODO The response from weatherdata is slightly different if looking at future weather report!
        # Test responses at various future times, verify that below keys still exist and get correct values
# [✓] getCDSChart
    # P3 TODO: Use more accurate distance model/equation
# [ ] getLocationData
    # P2 [ ] TODO: Distance and elevation calls should probably be two methods
    # P0 [ ] TODO: Both GMaps API calls VERY slow... why?
# [ ] calculateRating
    # P4 [ ] TODO Equation for calulcating the rating needs some work.
# [ ] getStargazeReport
    # P3 [ ] TODO User-facing message that time was changed to ___ (w/ TZ adjust!)


def getDarknessTimes(lat_selected, lon_selected, time):
    """Get times of day's darkness start/stop as unix time

    args: String representing lat/lon coords
    returns: Int of 10-digit Unix Time (integer seconds)
    """
    # TODO: Currently only returns darkness times for today, must work for next 48 hours
    # API accepts date paramter but in YYYY-MM-DD format, not unix time
    sunset_data = sunrise_sunset_time_api(lat_selected, lon_selected, time)

    # TODO: These times may be meaningless above/below (An)arctic Circle.
    # Check what API results are for arctic locations at different times of year
    # If Midnight Sun, tell user no stargazing possible :(
    # If Polar Night, they can stargaze whenever they want! :)

    # TODO: I just found out the times here dont explicitly account for Daylight Savings.
    # This may or may not be an issue...

    # start of astronomical twilight is good enough to begin stargazing
    # Nautical Twilight End = Start of Astronomical Twilight and vice-versa
    morning_stagazing_ends = sunset_data['results']['nautical_twilight_begin']
    night_stagazing_begins = sunset_data['results']['nautical_twilight_end']

    morning_stagazing_ends = dt.strptime(morning_stagazing_ends[:-6], '%Y-%m-%dT%H:%M:%S')
    night_stagazing_begins = dt.strptime(night_stagazing_begins[:-6], '%Y-%m-%dT%H:%M:%S')

    morning_stagazing_ends_unix = int((morning_stagazing_ends - dt(1970, 1, 1)).total_seconds())
    night_stagazing_begins_unix = int((night_stagazing_begins - dt(1970, 1, 1)).total_seconds())

    # print("sg Start @:",morning_stagazing_ends_unix)
    # print("sg end   @:",night_stagazing_begins_unix)

    return (morning_stagazing_ends_unix, night_stagazing_begins_unix)


def isDark(morning_stagazing_ends_unix, night_stagazing_begins_unix, curr_time_unix):
    """Checks if it is currently dark enough for stargazing

    args: Unix times for current time, darkness start/end time
    returns: Boolean
    """
    # pretty print(for debugging)
    # debug.ppWhenInDayNightCycle(morning_stagazing_ends_unix, curr_time_unix, night_stagazing_begins_unix)

    # Check if time is during the night or not
    # morning_stagazing_ends_unix = end of astronomical twilight
    # night_stagazing_begins_unix = start of astronomical
    # THEREFORE: Inbetween values is Day, Outside is Night!
    if curr_time_unix <= morning_stagazing_ends_unix or curr_time_unix >= night_stagazing_begins_unix:
        # Dark enough for stargazing
        # print("NIGHT\n")
        return True
    else:
        # Not dark enough yet
        # print("NO NIGHT YET\n")
        return False

def getWeatherAtTime(lat_selected, lon_selected, time=None):
    """Gets Weather report for location and time specified.

    args: lat/lon and time for stargazing site
    returns: dictionary with just the weather data we're interested in
    """
    # TODO: ONLY get data we need from API requests? Would be faster but requires
    # a lot more params in url request used. Probably worth it in the long run
    weatherdata = dark_sky_api(lat_selected, lon_selected, time)

    # debug.testDSAPI(weatherdata)

    # NOTE Hourly forcast data is only availible for next 48 hours
    # If more than 48 hours ahead, only have daily weather, so just assume it applies at night

    # TODO The response from weatherdata is slightly different if looking at future weather report!
    # Test responses at various future times, verify that below keys still exist and get correct values
    precip_prob = weatherdata['currently']['precipProbability']
    humidity = weatherdata['currently']['humidity']
    visibility = weatherdata['currently']['visibility']
    cloud_cover = weatherdata['currently']['cloudCover']
    moon_phase = weatherdata['daily']['data'][0]['moonPhase'] #0 tells to grab todays phase. allows 0-7 for phases over next week


    return {
        "precipProb":precip_prob,
        "humidity":humidity,
        "visibility":visibility,
        "cloudCover":cloud_cover,
        "moonPhase":moon_phase,
    }


#TODO: Distance and elevation calls should probably be two methods
def getLocationData(lat_origin, lon_origin, lat_selected, lon_selected):
    """Gets the elevation and distance to the given coordinates.

    args: lat/lon for origin and stargazing site selcted
    returns: dictionary with elevation, distance in time and space, simple units and human readable
    """

    dist_data = gmaps_distance_api(lat_origin, lon_origin, lat_selected, lon_selected)
    elev_data = gmaps_elevation_api(lat_selected, lon_selected)


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

    location_data = {
        "elevation": elev_data['results'][0]['elevation'],
        "duration_text": duration_text,
        "duration_value": duration_value,
        "distance_text": distance_text,
        "distance_value": distance_value,
    }

    return location_data


def siteRatingDescipt(site_quality):
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
      site_quality_discript = "Error: Select a site again"
    return site_quality_discript


def calculateRating(precipProbability, humidity, cloudCover, lightPol):
    """ Calculate the stargazing quality based off weather, light pollution, etc.

    args: site statistics, light pollution
    returns: Double rating from 0 - 100
    """
    # TODO Equation for calulcating the rating needs some work.
    # 7 percent cloud cover and otherwise perfect conditions should not be a rating of 77, Fair.

    # Rate quality based on each parameter
    precip_quality = (1-math.sqrt(precipProbability))
    humid_quality = (math.pow(-humidity+1,(1/3)))
    cloud_quality = (1-math.sqrt(cloudCover))
    lightpol_quality = (abs(50-lightPol)/50) #should give rating between 0.9995 (Middle of Nowhere) - 0.0646 (Downtown LA)

    #Find overall site quality using weighted average
    site_quality_rating = ((((precip_quality * lightpol_quality * cloud_quality)*8) + (humid_quality*2))/10)*100

    return site_quality_rating


#TODO: CleanUp/Refactor
@app.route("/stargazr")
def getStargazeReport(lat_org, lon_org, lat_starsite, lon_starsite, time=None):
    """get stargazing report based on given coordinates.

    args:
    lat_org/lon_org: gps coords of origin (user location) as float
    lat_starsite/lon_starsite: gps coords of selected stargazing site as float
    time: in unix int

    returns: dictionary with data needed for API response/display in front end
    """
    morning_stagazing_ends_unix, night_stagazing_begins_unix = getDarknessTimes(lat_starsite, lon_starsite, time)

    curr_time = getCurrentUnixTime()

    # If no time is given, first set time to current time.
    if not time:
        time = curr_time
    # If it is not dark at 'time', then set time to once it gets dark
    if not isDark(morning_stagazing_ends_unix, night_stagazing_begins_unix, time):
        time = night_stagazing_begins_unix
        #TODO User-facing message that time was changed to ___ (w/ TZ adjust!)

    weatherData = getWeatherAtTime(lat_starsite, lon_starsite, time)

    precip_prob = weatherData["precipProb"]
    humidity = weatherData["humidity"]
    cloud_cover = weatherData["cloudCover"]
    lunar_phase = weatherData["moonPhase"]
    light_pol = light_pollution_api(float(lat_starsite),float(lon_starsite))
    site_quality =  calculateRating(precip_prob, humidity, cloud_cover, light_pol)
    site_quality_discript = siteRatingDescipt(site_quality)

    #Only get CDS chart if time is within 24 hours
    if time < curr_time + 86000:
        cds_chart = nearest_csc_api(float(lat_starsite),float(lon_starsite))
    else:
        cds_chart = None

    siteData = {
        "siteQuality": site_quality,
        "siteQualityDiscript": site_quality_discript,
        "precipProb": precip_prob,
        "humidity": humidity,
        "cloudCover": cloud_cover,
        "lightPol": light_pol,
        "lunarphase": lunar_phase,
        "CDSChart": cds_chart
    }

    location_data = getLocationData(lat_org, lon_org, lat_starsite, lon_starsite)
    siteData.update(location_data)

    return json.dumps(siteData)

@app.route("/test")
def test():
    time = getCurrentUnixTime()

    # Test stargazing using San Francisco as user location, Pt Reyes at stargazing site, no time param
    result = getStargazeReport(37.7360512,-122.4997348, 38.116947, -122.925357)
    print("********** SF-Pt. Reyes TEST w/o time **********")
    print(result,"\n")

    # Test stargazing using San Francisco as user location, Stony Gorge at stargazing site, time is in 12 hr
    result = getStargazeReport(37.7360512,-122.4997348, 39.580110, -122.524105, time+43000)
    print("********** SF-Stony Gorge w/ time **********")
    print(result,"\n")

    # Test stargazing using San Francisco as user location, Pt Reyes at stargazing site, time is in 24 hr
    result = getStargazeReport(37.7360512,-122.4997348, 38.116947, -122.925357, time+86000)
    print("********** SF-Pt. Reyes w/ time **********")
    print(result,"\n")

    # Test stargazing using San Francisco as user location, Stony Gorge at stargazing site, time is in 36 hr
    result = getStargazeReport(37.7360512,-122.4997348, 39.580110, -122.524105, time+129000)
    print("********** SF-Stony Gorge w/ time **********")
    print(result,"\n")
    return

if __name__ == "__main__":
    test()
