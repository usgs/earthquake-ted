#!/usr/bin/env python

import os.path
import configparser
import logging.handlers

"""
trigger_funcs.py - Functions used in trigger.py, the application for generating TED messages.
"""

def create_logger(d):
    """
    Creates logfile using Python's logging module and saves to a 'log' directory. Uses timed 
    rotating file handler to archive logfile under a different name within the log directory, 
    create a new empty one, and delete all archived logfiles once a maximum number of archived
    files has been reached. 
    Returns logger object.
    d: Dictionary containing the following fields
       - bkup_inttype One character designating type of interval logfile will be archived 
         after (i.e., 'D' is day, 'M' is month)
       - bkup_interval Integer, amount of specified interval logfile will be archived after 
         (i.e., if bkup_inttype = 'D' and bkup_interval = 30, the file will be 
         archived after 30 days)
       - bkup_count Integer, how many backup logfiles to keep until all will be deleted 
       - bkup_suffix String, date format that will be appended to logfile when it is archived
       - homedir String, filepath
       - config ConfigParser object, points to config file
    """
    homedir = d['homedir']
    config = d['config']
    bkup_inttype = d['bkup_inttype']
    bkup_interval = d['bkup_interval']
    bkup_count = d['bkup_count']
    bkup_suffix = d['bkup_suffix']

    # Define logfile location and create logger object
    if not os.path.exists('log'):
        os.makedirs('log')
    log_dirpath = os.path.join(homedir, 'log')
    logfile = os.path.join(log_dirpath, config.get('SETUP','logfile'))
    logger = logging.getLogger(__name__)

    # Decide format messages will appear as in log and create formatter
    log_format = "%(asctime)s %(levelname)s - %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    main_formatter = logging.Formatter(fmt=log_format,datefmt=log_datefmt)

    # Create error file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(filename=logfile,
                   when=bkup_inttype,interval=bkup_interval,backupCount=bkup_count)
    file_handler.suffix = bkup_suffix
    file_handler.setFormatter(main_formatter)
    logger.addHandler(file_handler)

    # Set highest message level that will be logged
    level = config.get('SETUP','logging_level')
    if level.upper() not in ['INFO', 'DEBUG', 'WARNING', 'ERROR']:
         print("""Invalid value set for logger_level in config file. Accepted values 
               include info, debug, warning, and error (lower or upper case). Setting 
               logger_level to INFO.""")
         logger.setLevel('INFO')
    else:
         logger.setLevel(level.upper())

    return logger

def get_region_name(lat, lon):
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

