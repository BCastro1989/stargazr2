"""
Various helper functions for debugging, pretty printing, etc

"""

def testDSAPI(weatherdata):
    """DEBUG function for ensuring sucessful call to DarkSky Weather API.

    args: json weatherdata from DarkSky API
    returns: None
    """
    print "*********************************"
    if 'error' in weatherdata.keys():
        print "DARKSKY API RESPONSE ERROR\nHTTP", weatherdata['code'], "-", weatherdata['error']
    else:
        print "DARKSKY API RESPONSE SUCESS\n"


def ppWhenInDayNightCycle(morning_stagazing_ends_unix, curr_time_unix, night_stagazing_begins_unix):
    """Pretty prints current time in relation to darkness start/stop times

    args: unix timestamp for current time, morning darkness ends, night darkness begins
    returns: None
    """
    times = {
    "prev stargaze_start": int(night_stagazing_begins_unix) - 86400,
    "stargaze_end       ": int(morning_stagazing_ends_unix),
    "***curr_time***    ": int(curr_time_unix),
    "stargaze_start     ": int(night_stagazing_begins_unix),
    "next stargaze_end  ": int(morning_stagazing_ends_unix) + 86400,
    }
    print "********* When Current time is in Day/Night Cycle? *********"
    for key, value in sorted(times.iteritems(), key=lambda (k,v): (v,k)):
        print "%s: %s" % (key, value)
        

def ppSiteRatingBreakdown( precipProbability, humidity, cloudCover, lightPol, precip_quality, humid_quality, cloud_quality, lightpol_quality, site_quality_rating):
    print "********* Site Rating Breakdown *********"
    print "precipProbability:", precipProbability, ">", str(round(precip_quality*100,1))+"%"
    print "humidity:", humidity, ">", str(round(humid_quality*100,1))+"%"
    print "cloudCover:", cloudCover, ">", str(round(cloud_quality*100,1))+"%"
    print "lightPol:", lightPol, ">", str(round(lightpol_quality*100,1))+"%"
    print "site_quality_rating:", str(round(site_quality_rating,1))+"%\n"
