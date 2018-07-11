def getFormattedFile(filename):
    with open(filename, 'r') as f:
        data = f.read()
        lines=data.split('\n')
        csc_data = []

        for line in lines:
            csc_location = line.split("|")
            if len(csc_location) == 4:
                print csc_location
                csc_dict = {
                    "id": csc_location[0],
                    "name": csc_location[1],
                    "lat": float(csc_location[2]),
                    "lon": float(csc_location[3]),
                }
                csc_data.append(csc_dict)

        return csc_data


csc_data = getFormattedFile("csc_coords.txt")

maxlat = max(csc_data, key=lambda x:x['lat'])
minlat = min(csc_data, key=lambda x:x['lat'])
maxlon = max(csc_data, key=lambda x:x['lon'])
minlon = min(csc_data, key=lambda x:x['lon'])

print "maxlat:", maxlat['lat']
print "minlat:", minlat['lat']
print "maxlon:", maxlon['lon']
print "minlon:", minlon['lon']
