#!/usr/bin/env python

import configparser
import psycopg2
import cartopy.crs as ccrs
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from cartopy.feature import NaturalEarthFeature, LAND, LAKES
import urllib.request as urllib
import json
import numpy as np
import string
from collections import Counter
import os
import sys
# Local imports 
from trigger_funcs import create_logger

"""
map_funcs - Functions for creating  maps of TED detections and earthquake events.
"""

def get_map_folderpath(detectionID):
     """
     Make sure map directory exists and return folder location for maps to be 
     saved to.
     """
     homedir = os.path.dirname(os.path.abspath(__file__))
     if not os.path.exists('map'):
         os.makedirs('map')
     
     detection_folder = 'map/'+str(detectionID)
     if not os.path.exists(detection_folder):
         os.makedirs(detection_folder)
     map_dirpath = os.path.join(homedir, detection_folder) 

     return(map_dirpath)

def call_create_logger():
    """
    Create the dictionary that is read into create_logger and return logger object.
    """
    homedir = os.path.dirname(os.path.abspath(__file__))
    configfile = os.path.join(homedir,'map_funcs_config.ini')
    config = configparser.ConfigParser()
    config.read_file(open(configfile))
    
    # Create dictionary to use when passing parameters into create_logger()
    logdict = {}

    # Instruct logging module when to back up logfile and create new, empty one
    # Logfile will be archived every 30 days, and only 12 will be kept at a time
    logdict['bkup_inttype'] = 'D'
    logdict['bkup_interval'] = 30
    logdict['bkup_count'] = 12
    logdict['bkup_suffix'] = '%Y-%m-%d_%H:%M:%S'
    logdict['homedir'] = homedir
    logdict['config'] = config

    logger = create_logger(logdict)

    return(logger)

def connect_to_db():
     """
     Use information from config file to connect to postgres database.
     Return database connection and cursor objects.
     """

     try: 
         homedir = os.path.dirname(os.path.abspath(__file__))
         configfile = os.path.join(homedir,'map_funcs_config.ini')
         config = configparser.ConfigParser()
         config.read_file(open(configfile))

         prefix = 'db'
         # port = config.get('DATABASE',prefix+'_port')
         port = 5432
         user = config.get('DATABASE',prefix+'_user')
         dbname = config.get('DATABASE',prefix+'_name')
         password = config.get('DATABASE',prefix+'_password')

         conn = psycopg2.connect(dbname=dbname,user=user,port=port,password=password)
         cur = conn.cursor() 
     
         return(conn,cur)
     except psycopg2.Error as e:
         logger.error("e")

def get_tweet_coordinates(detectionID, logger):
    """
    Finds all of the tweets that triggered the detection, and returns their 
    lat/lon coordinates.
  
    detectionID: unique number corresponding to TED detection
    logger: logging object

    Returns: - tweetLats: list of floats, latitudinal coordinates of tweets
             - tweetLons: list of floats, longitudinal coordiantes of tweets
             - countCoords: integer, how many sets of tweet lats and lons 
                            that are being returned
    """
    conn, cur = connect_to_db()

    tweetLats = []
    tweetLons = []
    
    # Query database -- will need to change this query once detection_message
    # table is set up on new TED Dev database
    query = ("select reverse_geo_code from detection_status where " + \
             "detection_id = %s and reverse_geo_code is not null;"                  
             % detectionID) # Check that tweet is also trigger?
    cur.execute(query)
    tweetLocations = [row[0] for row in cur.fetchall()]
    
    if not tweetLocations:
        logger.info("No tweet coordinates available for this detection")
        conn.close()
        cur.close()
        sys.exit(0)
    
    # Get rid of any coordinates with letters
    tweetCoordinates = [x for x in tweetLocations if all(j.isdigit() or j \
                        in string.punctuation or j.isspace() for j in x)]

    # Split  tweet coordinates up into lat and lon lists
    splitTweetCoords = []

    for x in range(0, len(tweetCoordinates)):
        row = [x.strip() for x in tweetCoordinates[x].split(', ')]
        splitTweetCoords.append(row)

    tweetLats = [item[0] for item in splitTweetCoords]
    tweetLons = [item[1] for item in splitTweetCoords]

    logger.info("Tweet latitudes from database are: %s", str(tweetLats))
    logger.info("Tweet longitudes from database are: %s", str(tweetLons))

    # Convert tweet coordinate lists from strings to doubles
    tweetLons = [float(x) for x in tweetLons]
    tweetLats = [float(x) for x in tweetLats]
    
    # Convert tweet coordinates from string to float
    for index, item in enumerate(tweetLats):
        tweetLats[index] = float(item)
    for index, item in enumerate(tweetLons):
        tweetLons[index] = float(item)
    countCoords = len(tweetLats)

    logger.info("Number of tweet coordinates returned: %s", str(countCoords))
    logger.info("Tweet latitudes returned to map_tweets: %s", str(tweetLats))
    logger.info("Tweet longitudes returned to map_tweets: %s", str(tweetLons))

    conn.close()
    cur.close()

    return(tweetLats, tweetLons, countCoords)

def get_tweet_map_boundaries(tweetLats, tweetLons):
    """
    Returns the boundaries for the triggering tweet map based on the locations of
    the triggering tweets.

    tweetLats, tweetLons: coordinates of triggering tweets

    Returns: - minLon: float, minimum longitudinal coordinate on map
             - maxLon: float, maximum longitudinal coordinate on map
             - minLat: float, minimum latudinal coordinate on map
             - maxLat: float, maximum latitudinal coordinate on map
    """
    tolerance = 5
    
    minLon = min(tweetLons) - tolerance
    maxLon = max(tweetLons) + tolerance
    minLat = min(tweetLats) - tolerance
    maxLat = max(tweetLats) + tolerance
 
    return(minLon, maxLon, minLat, maxLat)

def get_cities(minPopulation, minLon, maxLon, minLat, maxLat, maxNumCities):
    """
    Uses USGS geoserve to find all of the cities within a given set of boundaries
    and with populations greater than a specified minimum population.

    minPopulation: integer, minimum population to compare cities to
    minLon, maxLon, minLat, maxLat: floats corresponding to map boundaries

    Returns: - cityNames: names of cities
             - cityLats, cityLons: coordinates of cities
    """
    jsonURL = ("https://earthquake.usgs.gov/ws/geoserve/places.json?" + \
              "minlatitude=" + format(minLat,'.5f') + "&maxlatitude=" + \
              format(maxLat,'.5f') + "&minlongitude=" + format(minLon,'.5f') + \
              "&maxlongitude=" + format(maxLon,'.5f') + "&minpopulation=" + \
              minPopulation + "&type=geonames")

    response = urllib.urlopen(jsonURL)
    geoserveData = json.load(response)

    cityNames = []
    cityLats = []
    cityLons = []
    cityPops = []

    cities = geoserveData["geonames"]["features"]
    cityCount = len(cities)
    for i in range(0,cityCount):
        cityNames.append(cities[i]["properties"]["name"])
        cityLons.append(cities[i]["geometry"]["coordinates"][0])
        cityLats.append(cities[i]["geometry"]["coordinates"][1])
        cityPops.append(cities[i]["properties"]["population"])

    # Check that each city is within defined search boundaries
    cityIndsToRemove = []
    newCityNames = []
    newCityLats = []
    newCityLons = []
    newCityPops = []
    for i in range(0,cityCount):
        if (cityLats[i] > maxLat or cityLats[i] < minLat or 
            cityLons[i] > maxLon or cityLons[i] < minLon):
            cityIndsToRemove += [i]
        
    for i in range(0,cityCount):
        if i not in cityIndsToRemove:
            newCityNames += [cityNames[i]]
            newCityLats += [cityLats[i]]
            newCityLons += [cityLons[i]]
            newCityPops += [cityPops[i]]
        
    # Replace city lists with new lists for cities in range
    cityNames = newCityNames
    cityLats = newCityLats
    cityLons = newCityLons
    cityPops = newCityPops
    cityCount = len(cityNames)

    # Increase population threshold if too many cities are returned
    # Decrease population threshold if not enough cities are returned
    minNumCities = 5
    while (cityCount > maxNumCities or minNumCities < minNumCities):
        if cityCount > maxNumCities:
            minPopulation = str(int(minPopulation) + 20000)
            cityNames, cityLons, cityLats, cityPops = get_cities(minPopulation, minLon,
                                                      maxLon, minLat, maxLat, maxNumCities)
            cityCount = len(cityNames)

        if cityCount < minNumCities:
            minPopulation = str(int(minPopulation) - 30000)
            cityNames, cityLons, cityLats, cityPops = get_cities(minPopulation, minLon,
                                                      maxLon, minLat, maxLat, maxNumCities)
            cityCount = len(cityNames)

    # Prevent cities from hiding each other on map by defining grid and comparing number
    # of cities in each grid cell. If there are multiple cities in a cell, throw away city/
    # cities with smallest population(s).
    numGridLines = 15 # in x and y directions 
    gridLons = np.linspace(minLon,maxLon,numGridLines) # location of x grid lines 
    gridLats = np.linspace(minLat,maxLat,numGridLines) # location of y grid lines
    numCitiesInGridCells = np.zeros((numGridLines,numGridLines)) 

    for i in range(0,numGridLines-1):
        for j in range(0,numGridLines-1):
            for k in range(0,cityCount):
                if (cityLats[k] >= gridLats[i] and cityLats[k] <= gridLats[i+1]
                    and cityLons[k] >= gridLons[j] and cityLons[k] <= gridLons[j+1]):
                    numCitiesInGridCells[i,j] += 1

    cityIndsToRemove = []
    for i in range(0,numGridLines-1):
        for j in range(0,numGridLines-1):
            if numCitiesInGridCells[i,j] > 1:
                listOfMultipleCityInds = []
                for k in range(0,len(cityNames)):
                    if (cityLats[k] >= gridLats[i] and cityLats[k] <= gridLats[i+1]
                        and cityLons[k] >= gridLons[j] and cityLons[k] <= gridLons[j+1]):
                        listOfMultipleCityInds += [k]
                cityIndWithMaxPop = 0
                index = 0
                maxPop = 0
                for n in range(0,len(listOfMultipleCityInds)):
                    index = listOfMultipleCityInds[n]
                    if (cityPops[index] > maxPop):
                        maxPop = cityPops[index]
                        cityIndWithMaxPop = index
                for m in range(0,len(listOfMultipleCityInds)): 
                    if listOfMultipleCityInds[m] != index:
                         cityIndsToRemove += [listOfMultipleCityInds[m]]

    newCityNames = []
    newCityLats = []
    newCityLons = []
    newCityPops = []
    for i in range(0,cityCount):
        if i not in cityIndsToRemove:
            newCityNames += [cityNames[i]]
            newCityLats += [cityLats[i]]
            newCityLons += [cityLons[i]]
            newCityPops += [cityPops[i]]

    return(newCityNames, newCityLons, newCityLats, newCityPops)

def map_detection(detectionID, basemap="terrain"):
    """
    Creates global map showing coordinates of TED detection and saves it within the map
    directory, in a folder with the same name as the detection ID.
   
    detectionID: unique number corresponding to TED detection 
    basemap: optional; accepted arguments include 'terrrain' and 'satellite', defines which 
             basemap will be used
    """
    # Open logfile
    logger = call_create_logger()
    
    try:
        # Query database for detection latitude and longitude
        conn, cur = connect_to_db()
        
        query = "select detection_lat, detection_lon from detection_ext where " + \
                "detection_id = " + str(detectionID)
        long_query = query + " union select 0,0 where not exists (" + \
                             query + ");"
        cur.execute(long_query)

        detection_coords = cur.fetchone()
        detectLat = detection_coords[0]
        detectLon = detection_coords[1]

        if detectLat == 0 or detectLon == 0:
            logger.info("No coordinates found in database for detection %i. Exiting",
                        detectionID)
            sys.exit(0)

        # Set path to backgrounds folder
        os.environ["CARTOPY_USER_BACKGROUNDS"] = "./images/"
    
        # Set map size and title
        plt.figure(figsize=(10,5))

        # Select the projection you want, plot the resolution you wish to use
        valid_options = ["terrain","satellite"]
        if basemap == "terrain":
            ax1 = plt.axes(projection=ccrs.PlateCarree())
            ax1.coastlines()
            ax1.stock_img() 
        elif basemap == "satellite":
            ax1 = plt.subplot(111,projection=ccrs.PlateCarree())
            ax1.background_img(name='satellite_small', resolution='high')
            ax1.coastlines(resolution='110m')
        else:
            warning_string = "No valid basemap option detected. Please enter" + \
                             "one of these options: %s. Exiting" % valid_options
            logger.warning(warning_string)
            sys.exit(1)

        # Plot detection as a point marker on the map
        plt.plot(detectLon, detectLat, color='red',
        marker='o',markersize=10,transform=ccrs.PlateCarree())
    
        # Display the plot in a window
        plt.title("TED Detection Location")

        # Save map
        map_dirpath = get_map_folderpath(detectionID)
        mapfile = os.path.join(map_dirpath,str(detectionID)+'_global_'+\
                               basemap+'.png')
        plt.savefig(mapfile)

        logger.info("Successfully created map for detection %i",
                     detectionID)        
        conn.close()
        cur.close()

    except Exception as e:
        logger.error("Error encountered while mapping detection", exc_info=True)
        conn.close()
        cur.close()

def map_tweets(detectionID, basemap="terrain"):
    """
    Maps the tweets that triggered a TED detection and saves it to a folder
    with the same name as the detection ID in a 'map' folder.
  
    detectionID: unique number corresponding to TED detection
    basemap: optional; accepted arguments include 'terrrain' and 'satellite', defines which 
             basemap will be used
    """
    # Open logfile
    logger = call_create_logger()

    try:
        tweetLats, tweetLons, countCoords = get_tweet_coordinates(detectionID, logger)
        minLon, maxLon, minLat, maxLat = get_tweet_map_boundaries(tweetLats, tweetLons)

        # Set path to backgrounds folder
        os.environ["CARTOPY_USER_BACKGROUNDS"] = "./images/"

        # Select the projection you want, plot the resolution you wish to use
        valid_options = ["terrain","satellite"]
        if basemap == "terrain":
            ax2 = plt.axes(projection=ccrs.PlateCarree())
            ax2.set_extent([minLon, maxLon, minLat, maxLat])
            ax2.stock_img()
            ax2.add_feature(LAND)
            ax2.add_feature(LAKES)
            ax2.coastlines(resolution='10m')

            # Add states/provinces
            STATES = NaturalEarthFeature(category='cultural',scale='10m',
                                         facecolor='none',
                                         name='admin_1_states_provinces_lines')
            ax2.add_feature(STATES,edgecolor='gray')
        elif basemap == "satellite":
            ax2 = plt.subplot(111,projection=ccrs.PlateCarree())
            ax2.background_img(name='satellite_large', resolution='high')
            ax2.set_extent([minLon, maxLon, minLat, maxLat])
        else:
            warning_string = "No valid basemap option detected. Please enter" + \
                             "one of these options: %s. Exiting" % valid_options
            logger.warning(warning_string)
            sys.exit(1)

        # Find duplicate tweet coordinates and make list of number of 
        # tweets at each location
        mapCoords = zip(tweetLons,tweetLats)
        countCoords = dict(Counter(mapCoords))
        tweetLons, tweetLats = zip(*countCoords.keys())

        # Plot the variables as a point marker on the map
        # Plot the first tweet separately so that marker appears in legend
        plt.plot(tweetLons[0], tweetLats[0], color='blue', linewidth=0,
                 marker='o',markersize=12,transform=ccrs.PlateCarree(),
                 label='Tweet')
        plt.plot(tweetLons, tweetLats, color='blue', linewidth=0,
                 marker='o',markersize=12,transform=ccrs.PlateCarree())

        # Label points with number of tweets
        dupCount = countCoords.values()
        for key in countCoords:
            plt.text(key[0], key[1], countCoords[key], fontsize=12, 
                     fontweight='bold', color='w', va='center', ha='center')

        # Get cities for map    
        minPopulation_tweetMap = "100000"
        maxNumCities = 10
        cityNames, cityLons, cityLats, cityPops = get_cities(minPopulation_tweetMap,
                                                  minLon, maxLon, minLat, maxLat,
                                                  maxNumCities)

        # Plot cities
        cityCount = len(cityNames)
        cmap = plt.cm.get_cmap('plasma',len(cityNames)) # colormap

        for i in range(0,cityCount):
            ax2.plot(cityLons[i], cityLats[i], color=cmap(i), linewidth=0,
                     marker='o', markersize=8,markeredgecolor = 'black',
                     markeredgewidth=0.6, transform=ccrs.PlateCarree(),
                     label=str(cityNames[i]))

        # Create legend outside of map to the right
        box = ax2.get_position()
        ax2.set_position([box.x0, box.y0, box.width * 0.7, box.height])
        ax2.legend(loc='center left', bbox_to_anchor=(1,0.5))

        # Display the plot in a window
        plt.title("Triggering Tweet Locations\n(With Number of Tweets at Each Location)")

        # Save map
        map_dirpath = os.path.join(get_map_folderpath(detectionID))
        mapfile = os.path.join(map_dirpath,str(detectionID)+'_tweets_'+\
                               basemap+'.png')
        plt.savefig(mapfile)

        logger.info("Successfully created triggering tweets map")

    except Exception as e:
        logger.error("Error encountered while mapping tweets", exc_info=True)

def map_event_vs_detection(detectionID, eventID, basemap="terrain"):
    """
    Maps TED detection and PDL event matches on the same regional map and saves it within the map
    directory, in a folder with the same name as the detection ID.

    detectionID: unique number corresponding to TED detection
    eventID: unique string corresponding to earthquake event
    basemap: optional; accepted arguments include 'terrrain' and 'satellite', defines which 
             basemap will be used
    """
    # Open logfile
    logger = call_create_logger()

    try:
        # Query database for detection and event information
        conn, cur = connect_to_db()
        query = """select detection_lat, detection_lon from detection_ext where detection_id 
                   = %i;""" % detectionID
        cur.execute(query)

        detection_coords = cur.fetchone()
        detectLat = float(detection_coords[0])
        detectLon = float(detection_coords[1])

        if detectLat == 0 or detectLon == 0:
            logger.info("No coordinates found in database for detection %i. Exiting",
                        detectionID)
            sys.exit(0)


        query = "select event_lat, event_lon from event_ext where event_id = '%s';" % eventID
        cur.execute(query)

        event_coords = cur.fetchone()
        eventLat = float(event_coords[0])
        eventLon = float(event_coords[1])

        if eventLat == 0 or eventLon == 0:
            logger.info("No coordinates found in database for event %s. Exiting", eventID)
            sys.exit(0)
 
        info_string = "Detection coordinates: '%.3f,%.3f' Event coordinates: '%.3f,%.3f'" % (
                      detectLat, detectLon, eventLat, eventLon)
        logger.info(info_string)

        # Define map boundaries
        tolerance = 5
        minLon = min(detectLon, eventLon) - tolerance
        maxLon = max(detectLon, eventLon) + tolerance
        minLat = min(detectLat, eventLat) - tolerance
        maxLat = max(detectLat, eventLat) + tolerance
        info_string = "City search boundaries: %.5f %.5f %.5f %.5f" % (
                      minLon, maxLon, minLat, maxLat) 
        logger.info(info_string)

        # Set path to backgrounds folder
        os.environ["CARTOPY_USER_BACKGROUNDS"] = "./images/"

        # Define a background image
        # Select the projection you want, plot the resolution you wish to use
        valid_options = ["terrain","satellite"]
        if basemap == "terrain":
            ax3 = plt.axes(projection=ccrs.PlateCarree())
            ax3.set_extent([minLon, maxLon, minLat, maxLat])
            ax3.stock_img()
            ax3.add_feature(LAND)
            ax3.add_feature(LAKES)
            ax3.coastlines(resolution='10m')

            # Add states/provinces
            STATES = NaturalEarthFeature(category='cultural',scale='10m',
                                         facecolor='none',
                                         name='admin_1_states_provinces_lines')
            ax3.add_feature(STATES,edgecolor='gray')
        elif basemap == "satellite":
            ax3 = plt.subplot(111,projection=ccrs.PlateCarree())
            ax3.background_img(name='satellite_large', resolution='high')
            ax3.set_extent([minLon, maxLon, minLat, maxLat])
        else:
            warning_string = "No valid basemap option detected. Please enter" + \
                             "one of these options: %s. Exiting" % valid_options
            logger.warning(warning_string)
            sys.exit(1)

        # Plot detection and event as point markers
        eventDot = plt.plot(eventLon, eventLat,
                            color='blue', linewidth=0, marker='o',
                            markersize=12, label="Event",
                            transform=ccrs.PlateCarree())
        detectDot = plt.plot(detectLon, detectLat, 
                             color='red', linewidth=0, marker='o',
                             markersize=12, label="Detection",
                             transform=ccrs.PlateCarree())

        # Get nearby cities for map
        minPopulation = "100000"
        maxNumCities = 10
        cityNames, cityLons, cityLats, cityPops = get_cities(minPopulation, minLon,
                                                  maxLon, minLat, maxLat, maxNumCities)

        logger.info("The following cities were returned to be mapped: %s", cityNames)
        logger.info("City latitudes: %s", cityLats)
        logger.info("City longitudes: %s", cityLons)
        logger.info("City populations: %s", cityPops)

        # Plot cities on map
        cityCount = len(cityNames)
        cmap = plt.cm.get_cmap('plasma',len(cityNames)) # colormap

        for i in range(0,cityCount):
            ax3.plot(cityLons[i], cityLats[i], color=cmap(i), linewidth=0,
                     marker='o', markersize=8,markeredgecolor = 'black',
                     markeredgewidth=0.6, transform=ccrs.PlateCarree(),
                     label=str(cityNames[i]))

        # Create legend outside of map to the right
        box = ax3.get_position()
        ax3.set_position([box.x0, box.y0, box.width * 0.7, box.height])
        ax3.legend(loc='center left', bbox_to_anchor=(1,0.5))

        # Display the plot in a window
        plt.title("Detection and Event Locations")

        # Save map
        map_dirpath = os.path.join(get_map_folderpath(detectionID))
        mapfile = os.path.join(map_dirpath,str(detectionID)+'_vs_'+eventID+'.png')
        mapfile = os.path.join(map_dirpath,str(detectionID)+'_vs_'+eventID+'_'+\
                               basemap+'.png')
        plt.savefig(mapfile)
        info_string = "Successfully created map of detection %i and event %s" % (
                      detectionID, eventID)
        logger.info(info_string)

        # Close connections
        conn.close()
        cur.close()

    except Exception as e:
        logger.error("Error encountered while mapping event match", exc_info=True)
        conn.close()
        cur.close()
