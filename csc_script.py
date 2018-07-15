def getFormattedCoordFile():
    with open("csc_coords.txt", 'r') as f:
        data = f.read()
        lines=data.split('\n')
        csc_data = []

        for line in lines:
            csc_location = line.split("|")
            if len(csc_location) == 4:
                # print csc_location
                csc_dict = {
                    "id": csc_location[0],
                    "loc": csc_location[1],
                    "lat": float(csc_location[2]),
                    "lon": float(csc_location[3]),
                }
                csc_data.append(csc_dict)

        return csc_data

def getFormattedNamesFile():
    with open("csc_title.txt", 'r') as f:
        data = f.read()
        lines=data.split('\n')
        csc_dict = {}

        for line in lines:
            csc_location = line.split("|")
            # print csc_location
            if len(csc_location) == 3:
                site_id = csc_location[0]
                csc_dict[site_id] = csc_location[2]

        return csc_dict


def makeBinnedJSON():
    pass

csc_data = getFormattedCoordFile()
csc_names = getFormattedNamesFile()

maxlat = max(csc_data, key=lambda x:x['lat'])
minlat = min(csc_data, key=lambda x:x['lat'])
maxlon = max(csc_data, key=lambda x:x['lon'])
minlon = min(csc_data, key=lambda x:x['lon'])

print "maxlat:", maxlat['lat']
print "minlat:", minlat['lat']
print "maxlon:", maxlon['lon']
print "minlon:", minlon['lon']

print len(csc_data)

from collections import defaultdict
import json
csc_binned = defaultdict(dict)

with open("csc_out.txt", 'w+') as f:
    for site in csc_data:
        site_name = csc_names[site["id"]]
        text_line = site["id"]+"|"+site_name+"|"+site["loc"]+"|"+str(site["lat"])+"|"+str(site["lon"])+"\n"
        f.write(text_line)

with open("csc_sites.json", 'w+') as f:
    for site in csc_data:
        site_name = csc_names[site["id"]]
        site_info = {
         "id": site["id"],
         "name": site_name,
         "loc": site["loc"],
         "lat": site["lat"],
         "lon": site["lon"]
         }

        if int(site["lon"]) not in csc_binned[int(site["lat"])]:
            csc_binned[int(site["lat"])][int(site["lon"])] = [site_info]
        else:
            csc_binned[int(site["lat"])][int(site["lon"])].append(site_info)
    json.dump(csc_binned, f)

print csc_binned
