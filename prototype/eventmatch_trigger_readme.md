eventmatch_trigger_readme.md

Introduction
------------

Eventmatch_trigger is an application which collects earthquake events that come in through PDL, adds them to a configurable Postgres table, and attempts to match the events to detections which already reside in the database.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated for whichever user is running PDL. The PDL runs this code when a new event or event update (origin product) is received. To activate this environment for that user, type:

    source activate ted

If the environment has not been created yet or does not exist, type:

    ./install.sh 

Two tables must exist in Postgres for events to be matched to detections:
- event_ext
- detection_ext
- event_match

If these tables have not been created, first activate the desired PostgreSQL database from the terminal by typing:

    psql -d <DB_name> -U <DB_user> -p <DB_port>

The values in brackets correspond to the values with the same name in eventmatch_config.ini. The user will also be asked to enter a password.

Create the event_ext table by typing:

    create sequence event_ext_id_seq;
    create table event_ext(
        id bigint not null primary key default nextval('event_ext_id_seq'),
        event_id character varying(40) not null,
        event_lat numeric(8,5),
        event_lon numeric(8,5),
        event_time timestamp without time zone,
        magnitude real
    );

Create the event_match table by typing:

    create sequence event_match_id_seq;
    create table event_match(
        id bigint not null primary key default nextval('event_match_id_seq'),
        detection_id bigint not null,
        event_id character varying(40)
        match_time timestamp without time zone,
        create_time timestamp without time zone
    );

If detection_ext has not already created, see detection_catcher_readme.md.

Eventmatch_trigger has been designed to run in Python 3.

Running eventmatch_trigger
--------------------------

To run eventmatch_trigger, first copy over eventmatch_trigger from ./bin into ~/tedapp. Make sure that trigger_funcs.py has been copied from ./ted into ~/tedapp.

The config file for eventmatch_trigger must be installed in ~/tedapp and named eventmatch_config.ini. An example eventmatch_config.ini can be found in this Git repository under ./exampleConfigFiles. The following pieces of information must be updated in the example eventmatch_config.ini to use it with eventmatch_trigger:

    db_ip          IP address of the Postgres database
    db_port        port number of the Postgres database
    db_name        name of the Postgres database
    db_user        username for the Postgres database
    db_password    password for the Postgres database

Eventmatch_trigger is instantiated by PDL, and needs its own indexer_listener and listener in the Product Client config file to run. 

    The config file for PDL should include something like this:

    [indexer_listener_exec_match]
    type = gov.usgs.earthquake.indexer.ExternalIndexerListener
    command = your/file/path/eventmatch_trigger
    storage = indexer_listener_exec_storage
    includeTypes = origin
    processDuplicateProducts = false
    processPreferredOnly = false
    autoArchive = true

And the line which begins with "listeners = " should include the new listener defined previously in brackets, like this:
 
    listeners = indexer_listener_exec, indexer_listener_exec_match

After editing config.ini, restart PDL.
