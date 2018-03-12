tweet_trigger_readme.md

Introduction
------------

Tweet_trigger is an application which collects earthquake events that come in through PDL and tweets them from a configurable Twitter account. For testing purposes, the notedalerts Twitter account was used. Tweet_trigger has been designed to run in Python 3. 

Installation and Dependencies
-----------------------------

Create a conda environment OR activate existing conda environment:
    To create a new environment, type: conda create --name anyEnvName
    To activate existing environment, type: source activate yourEnvName

Install dependencies by typing:
    pip install psycopg2
    pip install tweepy

Make sure this conda environment is activated for whatever user is running PDL. This is because the PDL client runs this code when a new event or event update (origin product) is received via PDL.

Running tweet_trigger.py
------------------------

To run tweet_trigger.py, you also must have configTweeter.ini installed in the same directory. This file must contain the necessary information to access the Twitter API and the tweet_audit table of the database. An example configTweeter.ini can be found in this Git repository, under .\bin\exampleConfigFiles\.

Tweet_trigger.py is instantiated by PDL, and needs its own indexer_listener and listener in the Product Client config file to run. 

    The config file for PDL should include something like this:

    [indexer_listener_exec_tweeter]
    type = gov.usgs.earthquake.indexer.ExternalIndexerListener
    command = your/file/path/tweet-trigger.py
    storage = indexer_listener_exec_storage
    includeTypes = origin
    processDuplicateProducts = false
    processPreferredOnly = false
    autoArchive = true

    And the line which begins with "listeners = " should include the new listener, like this:
 
    listeners = indexer_listener_exec, indexer_listener_exec_tweeter

