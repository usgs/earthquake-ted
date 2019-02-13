#!/usr/bin/env python

import os.path
import logging.handlers
from pathlib import Path
import subprocess
import time

"""
tedect.py - Functions used in tedect
"""


#######################################################################
#######################################################################
def log_section_dictionary_info(configfile, logger, setup_dict, logging_dict,
                                db_dict, esri_dict, mail_dict):
    """
    Purpose: writes content of config file section dictionary
             to the log file.  
             Note: does not show the database password

    Arguments: None

    Returns: None
    """

    # write the data dictionary key/value pairs to the log file
    log_msg = "Parameters in .ini file '{}'"
    log_msg = log_msg.format(configfile)
    logger.info(log_msg)
    section = "SETUP"
    log_msg = "  {} section:"
    log_msg = log_msg.format(section)
    logger.info(log_msg)
    for key in setup_dict:
        if (setup_dict[key] is None):
            log_msg = "    {} = None"
            log_msg = log_msg.format(key)
        else:
            log_msg = "    {} = {}"
            log_msg = log_msg.format(key, setup_dict[key])
        logger.info(log_msg)

    section = "LOGGING"
    log_msg = "  {} section:"
    log_msg = log_msg.format(section)
    logger.info(log_msg)
    for key in logging_dict:
        if (logging_dict[key] is None):
            log_msg = "    {} = None"
            log_msg = log_msg.format(key)
        else:
            log_msg = "    {} = {}"
            log_msg = log_msg.format(key, logging_dict[key])
        logger.info(log_msg)

    section = "DATABASE"
    log_msg = "  {} section:"
    log_msg = log_msg.format(section)
    logger.info(log_msg)
    for key in db_dict:
        if (key == 'password' ):
            log_msg = "    {} = **********"
            log_msg = log_msg.format(key)
        else:
            log_msg = "    {} = {}"
            log_msg = log_msg.format(key, db_dict[key])
        logger.info(log_msg)

    section = "ESRI"
    log_msg = "  {} section:"
    log_msg = log_msg.format(section)
    logger.info(log_msg)
    for key in esri_dict:
        if (esri_dict[key] is None):
            log_msg = "    {} = None"
            log_msg = log_msg.format(key)
        else:
            log_msg = "    {} = {}"
            log_msg = log_msg.format(key, esri_dict[key])
        logger.info(log_msg)

    section = "MAIL"
    log_msg = "  {} section:"
    log_msg = log_msg.format(section)
    logger.info(log_msg)
    for key in mail_dict:
        if (mail_dict[key] is None):
            log_msg = "    {} = None"
            log_msg = log_msg.format(key)
        else:
            log_msg = "    {} = {}"
            log_msg = log_msg.format(key, mail_dict[key])
        logger.info(log_msg)

    return


#######################################################################
#######################################################################
def start_logging(home_dir, logging_dict):    
    """
    Creates logfile using Python's logging module and saves to a 'log'
    directory.  Uses timed rotating file handler to archive logfile under
    a different name within the log directory, create a new empty one,
    and delete all archived logfiles once a maximum number of archived
    files has been reached.
    Returns logger object.
    """

    # set rotation parameters
    my_when = 'd'
    my_interval = 1
    my_backupCount = 21

    # Define logfile location and create logger object
    log_dirpath = os.path.join(home_dir, logging_dict['log_directory'])
    if not os.path.exists(log_dirpath):
        try:
            os.mkdir(log_dirpath)
            print('created ' + log_dirpath)
        except OSError as ex:
                log_msg = 'error {}  happened trying to create log dir'
                log_msg = log_msg.format(str(ex))
                print(log_msg)
                sys.exit(1)

    logfile = os.path.join(log_dirpath, logging_dict['logfile_name'])
    logger = logging.getLogger(__name__)

    # Decide format messages will appear as in log and create formatter
    log_format = "%(asctime)s %(levelname)s - %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    main_formatter = logging.Formatter(fmt = log_format, datefmt = log_datefmt)

    # Create error file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(filename = logfile,
                                                             when = my_when,
                                                             interval = my_interval,
                                                             backupCount = my_backupCount)
    file_handler.suffix = '%Y-%m-%d_%H:%M:%S'
    file_handler.setFormatter(main_formatter)
    logger.addHandler(file_handler)

    # Set highest message level that will be logged
    level = logging_dict['logging_level']
    if level.upper() not in ['INFO', 'DEBUG', 'WARNING', 'ERROR']:
        log_msg = ("Invalid value set for logger_level in SETUP section of"
                   " config file.  Accepted values include info, debug,"
                   " warning, and error (lower or upper case)."
                   " Setting logger_level to INFO.")
        print(log_msg)
        logger.setLevel('INFO')
    else:
         logger.setLevel(level.upper())

    log_msg = 'TimedRotatingFileHandler created:'
    logger.info(log_msg)
    log_msg = '\tParameters - when: {}  interval: {}  backupCount: {}'
    log_msg = log_msg.format(my_when, my_interval, my_backupCount)
    logger.info(log_msg)

    return logger

