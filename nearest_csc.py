import json
import math
import os

PATH = "csc_data"
FILENAME = "csc_sites.json"
MAX_DIST_KM = 100


def calc_great_circle_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two latitude-longitide points on sphere in kilometres.

    Assuming the Earth as a perfect sphere of radius 6371 km, calculate the distances between
    two latitude and longitutde coordinates on the Earth. Fairly accurate for distances under 100km.

    args: Float lat/lng for two points on Earth
    returns: Float representing distance in kilometres
    """
    R = 6371  # Earth Radius in kilometres (assume perfect sphere)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2-lat1)
    d_lambda = math.radians(lng2-lng1)

    a = math.sin(d_phi/2) * math.sin(d_phi/2) + math.cos(phi1) * \
        math.cos(phi2) * math.sin(d_lambda/2) * math.sin(d_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c

    return round(d, 1)  # Assume Accurate within ~0.1km due to Idealized Sphere Earth


def get_nearest_csc(lat, lng):
    """Nearest Clear Sky Chart from A. Danko's site: https://www.cleardarksky.com/

    All 5000+ sities are binned by 1x1 degree lat/lng. Only check the
    distance to sites within current bin +/- 1 degree, searching 9 bins total.

    args: request object w/ args for lat/lng
    returns: String, either with json representation of nearest site information or an error message
    """

    file_path = os.path.join(PATH, FILENAME)
    closest_site = {}

    # Get list of all csc site locations
    with open(file_path, 'r') as f:
        data = json.load(f)
        nearby_csc = []

        # Get list of all sites within same or adjacent 1 degree lat/lng bin
        try:
            for x in range(-1, 2):
                for y in range(-1, 2):
                    lat_str = str(int(lat)+x)
                    lng_str = str(int(lng)+y)
                    if lat_str in data:
                        if lng_str in data[lat_str]:
                            sites_in_bin = data[lat_str][lng_str]
                            for site in sites_in_bin:
                                nearby_csc.append(site)
        except:
            # API returns error
            closest_site = {'status': "ERROR parsing coordinates or reading from list of CSC sites"}

        curr_closest_km = MAX_DIST_KM

        # Find the closest site in Clear Dark Sky database within bins
        for site in nearby_csc:
            dist = calc_great_circle_distance(lat, lng, site["lat"], site["lon"])

            if dist < curr_closest_km:
                curr_closest_km = dist
                closest_site = site

        # Grab site url and return site data if within 100 km
        if curr_closest_km < MAX_DIST_KM:
            closest_site['status'] = "SUCCESS"
            closest_site['dist_km'] = curr_closest_km
            closest_site['full_img'] = "https://www.cleardarksky.com/c/"+closest_site['id']+"csk.gif"
            closest_site['mini_img'] = "https://www.cleardarksky.com/c/"+closest_site['id']+"cs0.gif"
        else:
            closest_site = {
                'status': "No sites within 100 km. CSC sites are only available in the Continental US, Canada, and Northern Mexico"
            }

        return closest_site
