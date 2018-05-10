map_funcs_readme.md

Introduction
------------

Quake_mapper maps TED detections and PDL earthquake events using the Python module Cartopy. Its methods still need to be integrated into event_trigger, eventmatch_trigger, and detection_catcher so that maps can be automatically created. It also needs to be tested more to ensure that high-quality maps are produced for all detections and events.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated to use this program. To activate this environment, type:
   
     source activate ted

If the environment has not been created yet or does not exist, type:

     ./install.sh

A detection_ext table must exist in Postgres before map_funcs can be run. If this table has not yet been created, see detection_catcher_readme.md. Quake_mapper has not been configured to work with the original detection table, because this table does not have columns for each detection's latitude and longitude coordinates, and detection_ext does.

Quake_mapper has been designed to run in Python 3.

Running map_funcs
-----------------

To run map_funcs, first copy over map_funcs from ./ted into ~/tedapp. Create a folder named 'images' in ~/tedapp and copy the files from ./images into this ~/tedapp/images. Make sure that trigger_funcs.py has been copied from ./ted into ~/tedapp.

The config file for map_funcs must be installed in ~/tedapp and named map_funcs_config.ini. An example map_funcs_config.ini can be found in this Git repository under ./exampleConfigFiles. The following pieces of information must be updated in the example map_funcs_config.ini to use it with map_funcs:

    db_ip          IP address of the Postgres database
    db_port        port number of the Postgres database
    db_name        name of the Postgres database
    db_user        username for the Postgres database
    db_password    password for the Postgres database

Quake_mapper's mapping functions are designed to be run individually based on which map is needed, but they could also be invoked in the trigger scripts in the future. 

To map the detection location with map_funcs, type the following command into your terminal (replace detectionID with the actual ID number):

    python -c 'from map_funcs import map_detection; map_detection(detectionID)'

To map the triggering tweet locations, type the following command into your terminal (replace detectionID with the actual ID number):

    python -c 'from map_funcs import map_tweets; map_tweets(detectionID)'

This function currently only works with the old TED Dev database and its detection_status table, so you will need to change the line that starts with 'port = ' in the connect_to_DB() method to 'port = 5432' if you want to create a tweet map. 

To map a detection that has been matched to an event (these are listed in the event_match table), type the following command into your terminal (replace detectionID with the actual ID number and eventID with the ID string):

    python -c 'from map_funcs import map_event_vs_detection; map_event_vs_detection(detectionID, "eventID")'

All mapping functions will produce maps with the terrain basemap as their default, but you can tell them to produce a Blue Marble image by adding "satellite" the last function argument. For example:

    python -c 'from map_funcs import map_detection; map_detection(detectionID, "satellite")

All maps will be saved to a map folder within the directory where the command was run, inside of a subfolder named after the detection ID the map was created for (for example, ~/tedapp/map/3127/).
