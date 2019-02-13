#!/usr/bin/env python

import configparser

"""
tedect_config_funcs.py - Functions used in tedect to support configuration
                         file validation
"""

#######################################################################
#######################################################################
def validate_config_file(config):
    """
    Purpose: Process config file to ensure all sections and key/value pairs.
             are present.  Also, initialize and load the data dictionaries
             for each section.

    Notes:   The configuration file is processed before logging starts
             (because the SETUP section contains logging parameters).
             Therefore, errors have to be printed to stdout (not the log
             file)
         
    Arguments: handle to config file

    Returns:   setup_dict, logging_dict, db_dict, esri_dict, mail_dict
    """

    # initialize the section dictionaries
    setup_dict = {}
    logging_dict = {}
    db_dict = {}
    esri_dict = {}
    mail_dict = {}

    # define the sections required and make sure they are present
    required_sections = ['SETUP', 'LOGGING', 'DATABASE', 'ESRI', 'MAIL']
    for section in required_sections:
        if not config.has_section(section):
            log_msg = "Config file '{}' is missing the '{}' section"
            log_msg = log_msg.format(configfile, section)
            print(log_msg)
            sys.exit(1)

    # validate [SETUP] section
    section = 'SETUP'
    keys = ['bin_length', 'lta_length', 'sta_length', 'm', 'b',
            'detection_threshold', 'trigger_reset', 'filter_terms',
            'max_words', 'bin_load_delay']
    missing = []
    for key in keys:
        if not config.has_option(section, key):
            missing.append(key)
        else:
            setup_dict[key] = config.get(section, key)
            if len(setup_dict[key]) == 0 :
                missing.append(key) 
    if len(missing):
        log_msg = ("[{}] section of Config file '{}' "
                   "is missing option(s): {}")
        log_msg = log_msg.format(section, configfile, ', '.join(missing))
        print(log_msg)
        sys.exit(1)

    # Validate the [LOGGING] section to make sure all required key/value
    # pairs are present.  Load the setup_dict along the way
    section = 'LOGGING'
    keys = ['logging_level', 'logfile_name', 'log_directory',
            'app_log_directory']
    missing = []
    for key in keys:
        if not config.has_option(section, key):
            missing.append(key)
        else:
            logging_dict[key] = config.get(section, key)
            if len(logging_dict[key]) == 0 :
                missing.append(key) 
    if len(missing):
        log_msg = ("[{}] section of Config file '{}' "
                   "is missing option(s): {}")
        log_msg = log_msg.format(section, configfile, ', '.join(missing))
        print(log_msg)
        sys.exit(1)

    # Validate the [DATABASE] section
    section = 'DATABASE'
    keys = ['port', 'user', 'name', 'password', 'ip']
    missing = []
    for key in keys:
        if not config.has_option(section, key):
            missing.append(key)
        else:
            db_dict[key] = config.get(section, key)
            if len(db_dict[key]) == 0 :
                missing.append(key) 
    if len(missing):
        log_msg = ("[{}] section of Config file '{}' "
                   "is missing option(s): {}")
        log_msg = log_msg.format(section, configfile, ', '.join(missing))
        print(log_msg)
        sys.exit(1)

    # Validate the [ESRI] section
    section = 'ESRI'
    keys = ['clientId', 'clientSecret']
    missing = []
    for key in keys:
        if not config.has_option(section, key):
            missing.append(key)
        else:
            esri_dict[key] = config.get(section, key)
            if len(esri_dict[key]) == 0 :
                missing.append(key) 
    if len(missing):
        log_msg = ("[{}] section of Config file '{}' "
                   "is missing option(s): {}")
        log_msg = log_msg.format(section, configfile, ', '.join(missing))
        print(log_msg)
        sys.exit(1)

    # Validate the [MAIL] section
    section = 'MAIL'
    keys = ['from', 'subject_tag', 'detection_list']
    missing = []
    for key in keys:
        if not config.has_option(section, key):
            missing.append(key)
        else:
            mail_dict[key] = config.get(section, key)
            if len(mail_dict[key]) == 0 :
                missing.append(key) 
    if len(missing):
        log_msg = ("[{}] section of Config file '{}' "
                   "is missing option(s): {}")
        log_msg = log_msg.format(section, configfile, ', '.join(missing))
        print(log_msg)
        sys.exit(1)

    return setup_dict, logging_dict, db_dict, esri_dict, mail_dict
