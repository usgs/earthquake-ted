#!/usr/bin/env python

import os.path
import configparser
import logging.handlers
import urllib.request
import json

"""
Twitter2Pg.py - Functions used in Twitter2Pg
"""

def create_logger(d):
    """
    Creates logfile using Python's logging module and saves to a 'log'
    directory.  Uses timed rotating file handler to archive logfile under
    a different name within the log directory, create a new empty one,
    and delete all archived logfiles once a maximum number of archived
    files has been reached.
    Returns logger object.
    d: Dictionary containing the following fields
       - bkup_inttype: One character designating type of interval logfile
                       will be archived after (i.e., 'D' is day, 'M' is month)
       - bkup_interval: Integer, amount of specified interval logfile will be
                        archived after (i.e., if bkup_inttype = 'D' and
                        bkup_interval = 30, the file will be archived after
                        30 days)
       - bkup_count: Integer, how many backup logfiles to keep until all will
                     be deleted
       - bkup_suffix: String, date format that will be appended to logfile when
                      it is archived
       - homedir: String, filepath
       - logfile_name: the logfile_name (from config file)
       - logging_level: the logging level (from config file)
       - log_directory: the name of the log directory (from config file)
    """
#    bkup_inttype = d['bkup_inttype']
#    bkup_interval = d['bkup_interval']
#    bkup_count = d['bkup_count']
#    bkup_suffix = d['bkup_suffix']

    # Define logfile location and create logger object
    log_dirpath = os.path.join(d['homedir'], d['log_directory'])
    if not os.path.exists(log_dirpath):
        try:
            os.mkdir(log_dirpath)
            print('created ' + log_dirpath)
        except OSError as ex:
                log_msg = 'error {}  happened trying to create log dir'
                log_msg = log_msg.format(str(ex))
                print(log_msg)
                sys.exit(1)

    logfile = os.path.join(log_dirpath, d['logfile_name'])
    logger = logging.getLogger(__name__)

    # Decide format messages will appear as in log and create formatter
    log_format = "%(asctime)s %(levelname)s - %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    main_formatter = logging.Formatter(fmt = log_format, datefmt = log_datefmt)

    # Create error file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(filename = logfile,
                   when = d['bkup_inttype'], interval = d['bkup_interval'],
                   backupCount = d['bkup_count'])
    file_handler.suffix = d['bkup_suffix']
    file_handler.setFormatter(main_formatter)
    logger.addHandler(file_handler)

    # Set highest message level that will be logged
    level = d['logging_level']
    if level.upper() not in ['INFO', 'DEBUG', 'WARNING', 'ERROR']:
        log_msg = ("Invalid value set for logger_level in SETUP section of"
                   " config file.  Accepted values include info, debug,"
                   " warning, and error (lower or upper case)."
                   " Setting logger_level to INFO.")
        print(log_msg)
        logger.setLevel('INFO')
    else:
         logger.setLevel(level.upper())

    return logger

