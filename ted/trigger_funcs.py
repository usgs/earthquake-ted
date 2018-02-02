"""
trigger_funcs.py - 
"""

def getRegionName(lat, lon):
    """
    Return the short version of the FE region name.
    lat: Latitude of input point.
    lat: Latitude of input point.
    Returns short form of the Flinn-Engdahl region name.
    """
    url = 'http://earthquake.usgs.gov/ws/geoserve/regions.json?latitude=LAT&longitude=LON&type=fe'
    url = url.replace('LAT', str(lat))
    url = url.replace('LON', str(lon))
    locstr = '%.3f, %.3f' % (lat, lon)
    try:
        fh = urllib.request.urlopen(url)
        regstr = fh.read()
        fh.close()
        jdict = json.loads(regstr)
        locstr = jdict['fe']['features'][0]['properties']['name']
    except:
        pass

    return locstr

