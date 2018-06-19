# TODO MAKE it so you can import this into a cmd line thing and get actual data from each thing
# Look at how to do authentication? or whatever??\
import requests
import math
import random
import pprint
from datetime import datetime as dt
import time
import iso8601 #DEPENDENCY

lat_selected = ""
lon_selected = ""

# elevation_url = "https://maps.googleapis.com/maps/api/elevation/json?locations="+lat_selected+","+lon_selected+"&key=AIzaSyAPV8hWJYamUd7TCnC6h6YcljuXnFW1lp8"
# #darksky_url = "http://stargazr.us-west-2.elasticbeanstalk.com/weather?lat="+lat_selected+"&lng="+lon_selected;
# darksky_url = "https://api.darksky.net/forecast/efc5a8359eb2564994acd4ec24971d4c/"+lat_selected+","+lon_selected
# lightpol_url = "http://stargazr.us-west-2.elasticbeanstalk.com/brightness?lat="+lat_selected+"&lng="+lon_selected;

#Things this API could use
#P0: SKY BRIGHTNESS = NO DAYTIME REPORTS!!!
#P1: URL for img of nearest CLEAR SKY Chart, none if > 100 miles, display distance to site (+name?)
#P2: TIME of Next ISS overpass + visibility
#P2: TIME of Iridium Flares + visibility
#P3: Any planets visible, where (specific + rough locations - i.e. az/art and general direction and height)



#GET WEATHER FOR THAT NIGHT
# Check time at location, check sunset at location, if before sunset, set to 1hour after sunset!
# Send alert message that this is the case
# EX, use:
# https://api.sunrise-sunset.org/json?lat=36.7201600&lng=-4.4203400&formatted=0
# BEFORE using DarkSky.

# STAGE 2: allow user to specify time?

def getAstroTwilight(lat_selected, lon_selected):
    sunset_url = "https://api.sunrise-sunset.org/json?lat=3"+lat_selected+"&lng="+lon_selected+"&formatted=0"
    print "ssurl", sunset_url
    request = requests.get(sunset_url)
    sunset_data = request.json()
    #start of astronomical twilight. Good enough to begin stargazing

    print sunset_data

    #Nautical Twilight End = Start of Astronomical Twilight and vice-versa
    astro_twilight_end = sunset_data['results']['nautical_twilight_begin'] #format:2015-05-21T20:28:21+00:00
    astro_twilight_start = sunset_data['results']['nautical_twilight_end']

    print "astro_twilight", astro_twilight_start, astro_twilight_end
    return (astro_twilight_start, astro_twilight_end)

def isDark(lat_selected, lon_selected):
    curr_time = dt.utcnow()#.isoformat()
    curr_time_unix = time.mktime(curr_time.timetuple())

    astro_start_time, astro_end_time = getAstroTwilight(lat_selected, lon_selected)
    print "astro_twilight", astro_start_time, astro_end_time
    astro_start_time = iso8601.parse_date(astro_start_time)
    astro_end_time = iso8601.parse_date(astro_end_time)

    astro_start_time_unix = time.mktime(astro_start_time.timetuple())
    astro_end_time_unix = time.mktime(astro_end_time.timetuple())
    print "astro_start", astro_start_time_unix
    print "curr_time  ", curr_time_unix
    print "astro_end  ", astro_end_time_unix
    # WATCH FOR TIME ZONES, DST ERRORS!
    # return max(curr_time, astro_start)

    # Check if time is during the day or not
    # AstroEnd = start of (almost) sunrise
    # AstroStart = end of (almost) sunset
    # THEREFORE: Inbetween values is Day, Outside is Night!

    if curr_time_unix >= astro_start_time_unix and curr_time_unix <= astro_end_time_unix:
        print "NIGHT"
        return True
    else:
        print "NO NIGHT YET"
        return False

def getLightPollutionTEST():
    lightpol_levels = [ 0.005, 0.035, 0.085, 0.15, 0.26, 0.455, 0.79, 1.365, 2.365, 4.1, 7.1, 12.295, 21.295, 36.895, 46.77]
    index = int(random.random()*len(lightpol_levels))%len(lightpol_levels)
    return lightpol_levels[index]

def getLightPollution():
    return getLightPollutionTEST()

def getWeather(lat_selected, lon_selected, time):
    darksky_url = "https://api.darksky.net/forecast/efc5a8359eb2564994acd4ec24971d4c/"+lat_selected+","+lon_selected+time
    print darksky_url
    request = requests.get(darksky_url)
    return request.json()

def getWeatherToday(lat_selected, lon_selected, time=""):
    if time:
        print "ADJUSTING TIME"
        time = ",time="+time
    weatherdata = getWeather(lat_selected, lon_selected, time)
    print weatherdata
    precipProbability = weatherdata['currently']['precipProbability']
    humidity = weatherdata['currently']['humidity']
    visibility = weatherdata['currently']['visibility']
    cloudCover = weatherdata['currently']['cloudCover']
    moonPhase = weatherdata['daily']['data'][0]['moonPhase'] #0 tells to grab todays phase. allows 0-7
    print cloudCover
    return {
        "precipProbability":precipProbability,
        "humidity":humidity,
        "visibility":visibility,
        "cloudCover":cloudCover,
        "moonPhase":moonPhase,
    }

def getCDSChart():
    pass

def getLocationData(lat_selected, lon_selected):
    '''
    get the site elevation, and distance
    '''
    maps_api_key = "AIzaSyAPV8hWJYamUd7TCnC6h6YcljuXnFW1lp8"

    #un-hardcode origin location
    dist_url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=San+Francisco,CA&destinations="+lat_selected+","+lon_selected+",NY&key="+maps_api_key
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
    #Rate quality based on each parameter
    precip_quality = (1-math.sqrt(precipProbability))
    humid_quality = (math.pow(-humidity+1,(1/3)))
    cloud_quality = (1-math.sqrt(cloudCover))
    lightpol_quality = (abs(50-lightPol)/50) #should give rating between 0.9995 (Middle of Nowhere) - 0.0646 (Downtown LA)
    print precipProbability, ">", precip_quality, "---", humidity, ">", humid_quality, "---", cloudCover, ">", cloud_quality, "---", lightPol, ">", lightpol_quality
    #Find overall site quality
    site_quality_rating = ((((precip_quality * lightpol_quality * cloud_quality)*8) + (humid_quality*2))/10)*100
    return site_quality_rating

#Expose via flask
def getStargazeReport(lat_selected,lon_selected):

    if not isDark(lat_selected, lon_selected):
        time = getAstroTwilight(lat_selected, lon_selected)

    weatherData = getWeatherToday(lat_selected, lon_selected, time) #allow for other days...

    precipProbability = weatherData["precipProbability"]
    humidity = weatherData["humidity"]
    cloudCover = weatherData["cloudCover"]
    lunarphase = weatherData["moonPhase"]

    lightPol = getLightPollution()

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

    location_data = getLocationData(lat_selected, lon_selected)
    siteData.update(location_data)

    return siteData

result = getStargazeReport("37.7360512","-122.4997348")
print "RESULT"
print pprint.pprint(result)
