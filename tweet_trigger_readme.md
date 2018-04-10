tweet_trigger_readme.md

Introduction
------------

Tweet_trigger is an application which collects earthquake events that come in through PDL and tweets them from a configurable Twitter account. For testing purposes, the notedalerts Twitter account was used.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated for whichever user is running PDL. The PDL runs this code when a new event or event update (origin product) is received. To activate this environment for that user, type:
    source activate ted
If the environment has not been created yet or does not exist, type:
    ./install.sh 

Tweet_trigger has been designed to run in Python 3.

Running tweet_trigger.py
------------------------

To run tweet_trigger.py, configTweeter.ini must be installed in the same directory. This file must contain the necessary information to access the Twitter API and the tweet_audit table of the database. An example configTweeter.ini can be found in this Git repository under .\bin\exampleConfigFiles\.

Tweet_trigger.py is instantiated by PDL, and needs its own indexer_listener and listener in the Product Client config file to run. 

    The config file for PDL should include something like this:

    [indexer_listener_exec_tweeter]
    type = gov.usgs.earthquake.indexer.ExternalIndexerListener
    command = your/file/path/tweet_trigger
    storage = indexer_listener_exec_storage
    includeTypes = origin
    processDuplicateProducts = false
    processPreferredOnly = false
    autoArchive = true

    And the line which begins with "listeners = " should include the new listener defined previously in brackets, like this:
 
    listeners = indexer_listener_exec, indexer_listener_exec_tweeter

