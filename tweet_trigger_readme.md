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

The tweet_audit tables must exist in Postgres. If this table has not been created yet, activate the desired PostgreSQL database from the terminal by typing:

    psql -d <DB_name> -U <DB_user> -p <DB_port>

And entering the same password that is used for the TED Dev database.
Create the tweet_audit table by typing:

    create sequence tweet_audit_id_seq;
    create table tweet_audit(
        id bigint not null primary key default nextval('tweet_audit_id_seq'),
        event_id character varying(40) not null,
        event_lat numeric(8,5),
        event_lon numeric(8,5),
        event_time timestamp without time zone,
        magnitude real,
        tweet_time timestamp without time zone not null
    );


Tweet_trigger has been designed to run in Python 3.

Running tweet_trigger
---------------------

To run tweet_trigger, first copy over tweet_trigger from ./bin into ~/tedapp. Make sure that trigger_funcs.py has been copied from ./ted into ~/tedapp.

The config file for tweet_trigger must be installed in ~/tedapp and named tweet_config.ini. An example tweet_config.ini can be found in this Git repository under ./exampleConfigFiles. The following pieces of information must be updated in the example tweet_config.ini to use it with tweet_trigger:

    gousa_username               Username associated with go.usa account for shortening links
    gousa_apikey                 Api key associated with go.usa account for shortening links
    db_ip          IP address of the Postgres database
    db_port        port number of the Postgres database
    db_name        name of the Postgres database
    db_user        username for the Postgres database
    db_password    password for the Postgres database
    twitter_apikey               Twitter API account key
    twitter_apisecret            Twitter API account secret key
    twitter_accesstoken          Twitter API account token
    twitter_accesstoken_secret   Twitter API account secret token

Tweet_trigger is instantiated by PDL, and needs its own indexer_listener and listener in the Product Client config file to run. 

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

After editing config.ini, restart PDL.
