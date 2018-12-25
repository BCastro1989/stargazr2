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
import json
import flask

#Things this API could use
#P0: [✓] No stargazing reports during the day
#P1: [✓] URL for img of nearest CLEAR SKY Chart, none if > 100 miles, display distance to site + name?
#P2: [✓] Allow user to specify what time to check?
#P3: [ ] TIME of Next ISS overpass + visibility, az/alt
#P4: [ ] TIME of Iridium Flares + visibility
#P4: [ ] Any planets visible, where (specific + rough locations - i.e. az/art and general direction and height)

#Front End Things to Worry about later
# Look at how to do authentication? HTTPS, SSL Key or whatever

def getCurrentUnixTime():
    """Get current time in UNIX format.

    args: none
    returns: String of 10-digit Unix Time (integer seconds)
    """
    return int(t.time())

#TODO: Depricate this?
def getFormattedDarknessTimes(lat_selected, lon_selected):
    """Get times of day's darkness start/stop. Formatted into human readable text

    args: String representing lat/lon coords
    returns: Unicide String of date and time in format: u'HH:MM:SS AM'
    """
    #Call sunrise-sunset API
    sunset_url = "https://api.sunrise-sunset.org/json?lat="+lat_selected+"&lng="+lon_selected
    request = requests.get(sunset_url)
    sunset_data = request.json()

    # morning_stagazing_ends when astronomical twilight ends and nautical_twilight_begins
    # night_stagazing_begins when astronomical twilight begins and nautical_twilight_ends
    morning_stagazing_ends = sunset_data['results']['nautical_twilight_begin'] #format:2015-05-21T20:28:21+00:00
    night_stagazing_begins = sunset_data['results']['nautical_twilight_end']

    print "stargaze_end", morning_stagazing_ends
    print "stargaze_start ", night_stagazing_begins

    return (morning_stagazing_ends, night_stagazing_begins)


def getDarknessTimes(lat_selected, lon_selected):
    """Get times of day's darkness start/stop. Formatted into human readable text

    args: String representing lat/lon coords
    returns: Int of 10-digit Unix Time (integer seconds)
    """
    sunset_url = "https://api.sunrise-sunset.org/json?lat="+lat_selected+"&lng="+lon_selected+"&formatted=0"

    request = requests.get(sunset_url)
    sunset_data = request.json()

    #start of astronomical twilight. Good enough to begin stargazing
    #Nautical Twilight End = Start of Astronomical Twilight and vice-versa
    morning_stagazing_ends = sunset_data['results']['nautical_twilight_begin']
    night_stagazing_begins = sunset_data['results']['nautical_twilight_end']

    morning_stagazing_ends = dt.strptime(morning_stagazing_ends[:-6], '%Y-%m-%dT%H:%M:%S')
    night_stagazing_begins = dt.strptime(night_stagazing_begins[:-6], '%Y-%m-%dT%H:%M:%S')

    morning_stagazing_ends_unix = int((morning_stagazing_ends - dt(1970, 1, 1)).total_seconds())
    night_stagazing_begins_unix = int((night_stagazing_begins - dt(1970, 1, 1)).total_seconds())

    return (morning_stagazing_ends_unix, night_stagazing_begins_unix)


def isDark(morning_stagazing_ends_unix, night_stagazing_begins_unix, curr_time_unix):
    """Checks if it is currently dark enough for stargazing

    args: Unix times for current time, darkness start/end time
    returns: Boolean
    """
    #pretty print for debugging
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
        return False


def getWeather(lat_selected, lon_selected, time):
    """Gets Weather report for location and time specified.

    args: lat/lon and time for stargazing site
    returns: weather api response in json format
    """
    darksky_url = "https://api.darksky.net/forecast/efc5a8359eb2564994acd4ec24971d4c/"+lat_selected+","+lon_selected+","+str(time)
    request = requests.get(darksky_url)
    return request.json()

#TODO: RENAME or CHANGE function b/c will allow to select future times for stargazing
def getWeatherToday(lat_selected, lon_selected, time):
    """Gets Weather report for location and time specified.

    args: lat/lon and time for stargazing site
    returns: dictionary with just the weather data we're interested in
    """
    #TODO: ONLY get data we need from API requests? Would be faster but requires
    # a lot more manipulation of the url request you use. Probably worth it
    weatherdata = getWeather(lat_selected, lon_selected, time)

    debug.testDSAPI(weatherdata)

    precip_prob = weatherdata['currently']['precipProbability']
    humidity = weatherdata['currently']['humidity']
    visibility = weatherdata['currently']['visibility']
    cloud_cover = weatherdata['currently']['cloudCover']
    moon_phase = weatherdata['daily']['data'][0]['moonPhase'] #0 tells to grab todays phase. allows 0-7

    return {
        "precipProb":precip_prob,
        "humidity":humidity,
        "visibility":visibility,
        "cloudCover":cloud_cover,
        "moonPhase":moon_phase,
    }


# DOUBLE CHECK THis MATH? at least be able to follow it
def latlonDistanceInKm(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/long points on globe in kilometres.

    args: lat/lon for two points on Earth
    returns: Float representing distance in kilometres
    """
    R = 6371 #Earth Radius in kilometres (assume perfect sphere)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2-lat1)
    d_lambda = math.radians(lon2-lon1)

    a = math.sin(d_phi/2) * math.sin(d_phi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2) * math.sin(d_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c

    return round(d,1) #Assume Accurate within 0.1km due to Idealized Sphere Earth

def getCDSChart(lat, lon):
    """Nearest Clear Dark Sky Chart from A. Danko's site

    args: String of lat/lon for stargazing site
    returns: Tuple of distance to closest CDSC site, and dict of site info. If
        no sites within 100km, return None
    """
    # get list of all csc site locations
    with open('csc_sites2.json', 'r') as f:
        data = json.load(f)
        nearby_cdsc = []
        print lat, lon
        #get list of all sites within same or adjacent 1 degree lat/lon bin
        try:
            for x in xrange(-1,2):
                for y in xrange(-1,2):
                    lat_str = str(int(lat+x))
                    lon_str = str(int(lon+y))
                    if lat_str in data:
                        if lon_str in data[lat_str]:
                            sites_in_bin = data[lat_str][lon_str]
                            for site in sites_in_bin:
                                nearby_cdsc.append(site)
        except:
            print "err"

        #Initialize vars
        closest_dist = 3 #in degrees, cant be more than 2.828, ot (2 * sqrt(2))
        closest_site = {}
        dist_km = 100

        #Find the closest site in CDSC database within bins
        for site in nearby_cdsc:
            site_lat = site["lat"]
            site_lon = site["lon"]
            dist = math.sqrt( (site_lat-lat)**2 + (site_lon-lon)**2 )
            if dist < closest_dist:
                closest_dist = dist
                closest_site = site
                dist_km = latlonDistanceInKm(lat, lon, site_lat, site_lon)

        #grab site url and return site data if within 100km
        if dist_km < 100:
            closest_site['dist_km'] = dist_km
            return closest_site

        return None

#TODO: Distance and elevation should probably be two meothds (since two calls)
def getLocationData(lat_selected, lon_selected):
    """Gets the elevation and distance to the given coordinates.

    args: lat/lon
    returns: dictionary with elevation, distance in time and space, simple units and human readable
    """
    maps_api_key = "AIzaSyAPV8hWJYamUd7TCnC6h6YcljuXnFW1lp8"

    #TODO: un-hardcode origin location
    dist_url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=San+Francisco,CA&destinations="+lat_selected+","+lon_selected+"&key="+maps_api_key
    elevation_url = "https://maps.googleapis.com/maps/api/elevation/json?locations="+lat_selected+","+lon_selected+"&key="+maps_api_key

    dist_request = requests.get(dist_url)
    elev_request = requests.get(elevation_url)

    dist_data = dist_request.json()
    elev_data = elev_request.json()

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
    # TODO Needs some work. 7 percent cloud cover and otherwise perfect conditions should not be a rating of 77
    # Rate quality based on each parameter
    precip_quality = (1-math.sqrt(precipProbability))
    humid_quality = (math.pow(-humidity+1,(1/3)))
    cloud_quality = (1-math.sqrt(cloudCover))
    lightpol_quality = (abs(50-lightPol)/50) #should give rating between 0.9995 (Middle of Nowhere) - 0.0646 (Downtown LA)

    #Find overall site quality
    site_quality_rating = ((((precip_quality * lightpol_quality * cloud_quality)*8) + (humid_quality*2))/10)*100

    debug.ppSiteRatingBreakdown(precipProbability, humidity, cloudCover, lightPol, precip_quality, humid_quality, cloud_quality, lightpol_quality, site_quality_rating)
    return site_quality_rating



#TODO: Expose via flask
#TODO: CleanUp/Refactor
def getStargazeReport(lat,lon,time=None):
    """get stargazing report based on given coordinates.

    args: lat/lon
    returns: dictionary with just data needed for front end by API
    """
    lat_str = str(lat)
    lon_str = str(lon)

    #No time is given, assume now or once it gets dark tonight
    if not time:
        curr_time_unix = getCurrentUnixTime()
        morning_stagazing_ends_unix, night_stagazing_begins_unix = getDarknessTimes(lat_str, lon_str)
        if isDark(morning_stagazing_ends_unix, night_stagazing_begins_unix, curr_time_unix):
            time = curr_time_unix
        else:
            time = getDarknessTimes(lat_str, lon_str)[1]
            #TODO User-facing message that time set to ___
            print "Not night time yet! Getting stargazing report for ", time

    weatherData = getWeatherToday(lat_str, lon_str, time) #allow for other days...

    precip_prob = weatherData["precipProb"]
    humidity = weatherData["humidity"]
    cloud_cover = weatherData["cloudCover"]
    lunarphase = weatherData["moonPhase"]
    cds_chart = getCDSChart(lat,lon)
    light_pol = getLightPollution(lat,lon)
    site_quality =  calculateRating(precip_prob, humidity, cloud_cover, light_pol)
    site_quality_discript = siteRatingDescipt(site_quality)

    siteData = {
        "siteQuality": site_quality,
        "siteQualityDiscript": site_quality_discript,
        "precipProb": precip_prob,
        "humidity": humidity,
        "cloudCover": cloud_cover,
        "lightPol": light_pol,
        "lunarphase": lunarphase,
        "CDSChart": cds_chart
    }

    location_data = getLocationData(lat_str, lon_str)
    siteData.update(location_data)

    return siteData

#Test stargazing in San Francisco
result = getStargazeReport(37.7360512,-122.4997348)#+86k=+1day
print "********** SF TEST **********"
print pprint.pprint(result)


#Test stargazing in San Francisco
result = getStargazeReport(37.7360512,-122.4997348, 1545673406)#+86k=+1day
print "********** SF TEST **********"
print pprint.pprint(result)

# #Test stargazing in Australian Outback
# result = getStargazeReport(-24.5906227,129.5304454)
# print "********** OZ TEST **********"
# print pprint.pprint(result)
