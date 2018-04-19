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

Running event_trigger
---------------------

To run event_trigger, first copy over event_trigger from ./bin/ into /home/ted/tedapp/. Make sure that trigger_funcs.py has been copied from ./ted/ into /home/ted/tedapp/.

The config file for event_trigger must be installed in the same directory and named event_config.ini. An example event_config.ini can be found in this Git repository under .\bin\exampleConfigFiles\. The following pieces of information must be updated in the example event_config.ini to use it with event_trigger:

    devtweetserver          update with the URL of the TED Dev server
    prodtweetserver         update with the URL of the TED Production server
    development_hostname    update with the host name of the machine whose name ends in 
                            m024
    test_hostname           update with the name of the TED Dev machine
    production_hostname     update with the name of the TED Production machine

Event_trigger is instantiated by PDL, and should already have its own indexer_listener and listener in the Product Client config file. The config file for PDL should already include something like this:

    [indexer_listener_exec]
    type = gov.usgs.earthquake.indexer.ExternalIndexerListener
    command = your/file/path/event_trigger
    storage = indexer_listener_exec_storage
    includeTypes = origin
    processDuplicateProducts = false
    processPreferredOnly = false
    autoArchive = true

And the line which begins with "listeners = " should already include the listener defined previously in brackets, like this:
 
    listeners = indexer_listener_exec

