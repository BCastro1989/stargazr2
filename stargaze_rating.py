#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import math
import pprint
from datetime import datetime as dt
import time as t
import iso8601 #DEPENDENCY pip install it
from light_pollution import getLightPollution
import debug


# elevation_url = "https://maps.googleapis.com/maps/api/elevation/json?locations="+lat_selected+","+lon_selected+"&key=AIzaSyAPV8hWJYamUd7TCnC6h6YcljuXnFW1lp8"
# #darksky_url = "http://stargazr.us-west-2.elasticbeanstalk.com/weather?lat="+lat_selected+"&lng="+lon_selected;
# darksky_url = "https://api.darksky.net/forecast/efc5a8359eb2564994acd4ec24971d4c/"+lat_selected+","+lon_selected
# lightpol_url = "http://stargazr.us-west-2.elasticbeanstalk.com/brightness?lat="+lat_selected+"&lng="+lon_selected;

#Things this API could use
#P0: [✓] No stargazing reports during the day
#P1: [ ] URL for img of nearest CLEAR SKY Chart, none if > 100 miles, display distance to site (+name?)
#P2: [ ] TIME of Next ISS overpass + visibility
#P2: [ ] TIME of Iridium Flares + visibility
#P3: [ ] Any planets visible, where (specific + rough locations - i.e. az/art and general direction and height)
#P4: [ ] Allow user to specify what time to check?

#Front End Things to Worry about later
# Look at how to do authentication? HTTPS, SSL Key or whatever


def getCurrentUnixTime():
    """Get current time in UNIX format.

    args: none
    returns: String of 10-digit Unix Time (integer seconds)

    """
    return str(t.mktime(dt.now().timetuple()))[:-2]


def getFormattedDarknessTimes(lat_selected, lon_selected):
    """Get times of day's darnkness start/stop. Formatted into human readable text

    """
    sunset_url = "https://api.sunrise-sunset.org/json?lat="+lat_selected+"&lng="+lon_selected
    # print "ssurl", sunset_url
    request = requests.get(sunset_url)
    sunset_data = request.json()
    morning_stagazing_ends = sunset_data['results']['nautical_twilight_begin'] #format:2015-05-21T20:28:21+00:00
    night_stagazing_begins = sunset_data['results']['nautical_twilight_end']

    print "stargaze_end", morning_stagazing_ends
    print "stargaze_start ", night_stagazing_begins

    return (morning_stagazing_ends, night_stagazing_begins)


def getDarknessTimes(lat_selected, lon_selected):
    sunset_url = "https://api.sunrise-sunset.org/json?lat="+lat_selected+"&lng="+lon_selected+"&formatted=0"
    request = requests.get(sunset_url)
    sunset_data = request.json()

    #start of astronomical twilight. Good enough to begin stargazing
    #Nautical Twilight End = Start of Astronomical Twilight and vice-versa
    morning_stagazing_ends = sunset_data['results']['nautical_twilight_begin'] #format:2015-05-21T20:28:21+00:00
    night_stagazing_begins = sunset_data['results']['nautical_twilight_end']

    # print "stargaze_end", morning_stagazing_ends[:-6]
    # print "stargaze_start ", night_stagazing_begins[:-6]

    morning_stagazing_ends = dt.strptime(morning_stagazing_ends[:-6], '%Y-%m-%dT%H:%M:%S')
    night_stagazing_begins = dt.strptime(night_stagazing_begins[:-6], '%Y-%m-%dT%H:%M:%S')

    morning_stagazing_ends_unix = str((morning_stagazing_ends - dt(1970, 1, 1)).total_seconds())[:-2]
    night_stagazing_begins_unix = str((night_stagazing_begins - dt(1970, 1, 1)).total_seconds())[:-2]

    return (morning_stagazing_ends_unix, night_stagazing_begins_unix)


def isDark(morning_stagazing_ends_unix, night_stagazing_begins_unix, curr_time_unix):
    """Checks if it is currently dark enough for stargazing

    args: Unix times for current time, sarkness start/end time
    returns: Boolean
    """
    #uugggghhh this is temporary okay
    debug.ppWhenInDayNightCycle(morning_stagazing_ends_unix, curr_time_unix, night_stagazing_begins_unix)

    # Check if time is during the night or not
    # morning_stagazing_ends_unix = end of astronomical twilight, ~1hr to sunrise
    # night_stagazing_begins_unix = start of astronomical, , ~1hr to sunset
    # THEREFORE: Inbetween values is Day, Outside is Night!
    if curr_time_unix <= morning_stagazing_ends_unix or curr_time_unix >= night_stagazing_begins_unix:
        # Dark enough for stargazing
        print "NIGHT\n"
        return True
    else:
        # Not dark enough yet
        print "NO NIGHT YET\n"
        # Send alert message that this is the case
        return False

def getWeather(lat_selected, lon_selected, time):
    """Gets Weather report for location and time specified.

    args: lat/lon and time for stargazing site
    returns: weather api response in json format
    """
    darksky_url = "https://api.darksky.net/forecast/efc5a8359eb2564994acd4ec24971d4c/"+lat_selected+","+lon_selected+","+time
    request = requests.get(darksky_url)
    return request.json()


def getWeatherToday(lat_selected, lon_selected, time):
    """RENAME? Not good name or change the function!
    Gets Weather report for location and time specified.

    args: lat/lon and time for stargazing site
    returns: dictionary with just Weather data we're interested in
    """
    #TODO: ONLY get data we need from API requests? Would be faster but requires
    # a lot more manipulation of the url request you use
    weatherdata = getWeather(lat_selected, lon_selected, time)

    debug.testDSAPI(weatherdata)

    precipProbability = weatherdata['currently']['precipProbability']
    humidity = weatherdata['currently']['humidity']
    visibility = weatherdata['currently']['visibility']
    cloudCover = weatherdata['currently']['cloudCover']
    moonPhase = weatherdata['daily']['data'][0]['moonPhase'] #0 tells to grab todays phase. allows 0-7
    return {
        "precipProbability":precipProbability,
        "humidity":humidity,
        "visibility":visibility,
        "cloudCover":cloudCover,
        "moonPhase":moonPhase,
    }


def getCDSChart():
    """Nearest Clear Dark Sky Chart from A. Danko's site

    args: lat/lon
    returns: url to CDSC image? link to regular site? both? what if none nearby?
    """
    #TODO: How to deal with locations well outside of any nearby CDSC?
    #TODO What exactly are re returning?
    pass


def getLocationData(lat_selected, lon_selected):
    """Gets the elevation and distance to the given coordinates

    args: lat/lon
    returns: dictionary with elevation, distance in time and space, simple units and human readable
    """
    maps_api_key = "AIzaSyAPV8hWJYamUd7TCnC6h6YcljuXnFW1lp8"

    #un-hardcode origin location
    dist_url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=San+Francisco,CA&destinations="+lat_selected+","+lon_selected+"&key="+maps_api_key
    elevation_url = "https://maps.googleapis.com/maps/api/elevation/json?locations="+lat_selected+","+lon_selected+"&key="+maps_api_key

    dist_request = requests.get(dist_url)
    elev_request = requests.get(elevation_url)

    dist_data = dist_request.json()
    elev_data = elev_request.json()

    location_data = {
        "elevation": elev_data['results'][0]['elevation'],
        "duration_text": dist_data['rows'][0]['elements'][0]['duration']['text'],
        "duration_value": dist_data['rows'][0]['elements'][0]['duration']['value'],
        "distance_text": dist_data['rows'][0]['elements'][0]['distance']['text'],
        "distance_value": dist_data['rows'][0]['elements'][0]['distance']['value'],
    }

    return location_data


def siteRatingDescipt(site_quality):
    """Describe the site based off it's rating

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
    """ Calculate the stargazing quality based off weather, light pollution, etc
    args: site statistics, light pollution
    returns: Double rating from 0 - 100
    """
    # TODO Needs some work. 7 percent cloud cover and otherwise perfect conditions should not be a rating of 77
    #Rate quality based on each parameter
    precip_quality = (1-math.sqrt(precipProbability))
    humid_quality = (math.pow(-humidity+1,(1/3)))
    cloud_quality = (1-math.sqrt(cloudCover))
    lightpol_quality = (abs(50-lightPol)/50) #should give rating between 0.9995 (Middle of Nowhere) - 0.0646 (Downtown LA)

    #Find overall site quality
    site_quality_rating = ((((precip_quality * lightpol_quality * cloud_quality)*8) + (humid_quality*2))/10)*100

    debug.ppSiteRatingBreakdown(precipProbability, humidity, cloudCover, lightPol, precip_quality, humid_quality, cloud_quality, lightpol_quality, site_quality_rating)
    return site_quality_rating


#Expose via flask
def getStargazeReport(lat_selected,lon_selected):
    lat_str = str(lat_selected)
    lon_str = str(lon_selected)
    """get stargazing report based on given coordinates
    args: lat/lon
    returns: dictionary with just data needed for front end by API
    """
    curr_time_unix = getCurrentUnixTime()
    morning_stagazing_ends_unix, night_stagazing_begins_unix = getDarknessTimes(lat_str, lon_str)

    if isDark(morning_stagazing_ends_unix, night_stagazing_begins_unix, curr_time_unix):
        time = curr_time_unix
    else:
        time = getDarknessTimes(lat_str, lon_str)[1]
        #TODO User-facing message that time set to ___
        print "Not night time yet! Getting stargazing report for ", time

    weatherData = getWeatherToday(lat_str, lon_str, time) #allow for other days...

    precipProbability = weatherData["precipProbability"]
    humidity = weatherData["humidity"]
    cloudCover = weatherData["cloudCover"]
    lunarphase = weatherData["moonPhase"]

    lightPol = getLightPollution(lat_selected, lon_selected)

    site_quality =  calculateRating(precipProbability, humidity, cloudCover, lightPol)
    site_quality_discript = siteRatingDescipt(site_quality)

    siteData = {
        "site_quality": site_quality,
        "site_quality_discript": site_quality_discript,
        "precipProbability": precipProbability,
        "humidity": humidity,
        "cloudCover": cloudCover,
        "lightPol": lightPol,
        "lunarphase": lunarphase,
    }

    location_data = getLocationData(lat_str, lon_str)
    siteData.update(location_data)

    return siteData

result = getStargazeReport(37.7360512,-122.4997348)
print "********** RESULT **********"
print pprint.pprint(result)
