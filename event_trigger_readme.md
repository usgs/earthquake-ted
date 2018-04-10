event_trigger_readme.md

Introduction
------------

Event_trigger is an application which collects earthquake events that come in through PDL and sends them to Tomcat.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated for whichever user is running PDL. The PDL runs this code when a new event or event update (origin product) is received. To activate this environment for that user, type:
    source activate ted
If the environment has not been created yet or does not exist, type:
    ./install.sh 

Event_trigger has been designed to run in Python 3.

Running event_trigger.py
------------------------

To run event_trigger.py, config.ini must be installed in the same directory. This file must contain the necessary information to access the Twitter API and the tweet_audit table of the database. An example config.ini can be found in this Git repository under .\bin\exampleConfigFiles\.

Event_trigger.py is instantiated by PDL, and should already have its own indexer_listener and listener in the Product Client config file.

    The config file for PDL should already include something like this:

    [indexer_listener_exec]
    type = gov.usgs.earthquake.indexer.ExternalIndexerListener
    command = your/file/path/eventmatch_trigger
    storage = indexer_listener_exec_storage
    includeTypes = origin
    processDuplicateProducts = false
    processPreferredOnly = false
    autoArchive = true

    And the line which begins with "listeners = " should already include the listener defined previously in brackets, like this:
 
    listeners = indexer_listener_exec

