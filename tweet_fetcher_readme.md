tweet_fetcher_readme.md

Introduction
------------

Tweet_fetcher is an application which establishes a tweet stream using the Twitter API, filters out tweets containing earthquake keywords, and adds these tweets to a Postgres table.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated for whichever user is running PDL. The PDL runs this code when a new event or event update (origin product) is received. To activate this environment for that user, type:

    source activate ted

If the environment has not been created yet or does not exist, type:

    ./install.sh 

The following tables must exist in Postgres:
- keyword
- message

If these tables have not been created, first activate the desired PostgreSQL database from the terminal by typing:

    psql -d <DB_name> -U <DB_user> -p <DB_port>

And entering the same password that is used for the TED Dev database.
Create the keyword table by typing:

    create table keyword(
        id integer not null primary key, 
        title character varying(60)
    );
    insert into keyword(id,title)
    values (1,'earthquake'),(2,'sismo'),(3,'quake'),(4,'temblor'),
           (5,'terremoto'),(6,'gempa'),(7,'lindol'),(8,'tremblement'),
           (9,'erdbeben'),(10,'deprem'),(11,'σεισμός'),(12,'seismós'),
           (13,'séisme'),(14,'zemljotres'),(15,'potres'),(16,'terremot'),
           (17,'jordskjelv'),(18,'cutremur'),(19,'aardbeving'),(20,'地震'),
           (21,'भूकंप'),(22,'زلزال'),(23,'tremor'),(24,'지진');

Create the message table by typing:

    create sequence message_id_seq;
    create table message(
        id bigint not null primary key default nextval('message_id_seq'),
        date_created timestamp without time zone not null,
        lang character varying(5),
        location_lat numeric(11,7),
        location_lon numeric(11,7),
        location_source character varying(10),
        location_string character varying(100),
        media_display_url character varying(255),
        media_type character varying(10),
        message_date timestamp without time zone not null,
        message_id bigint,
        message_source character varying(20) not null,
        message_text character varying(290),
        time_zone character varying(80),
        utc_offset bigint,
        word_count integer
    );

Tweet_fetcher has been designed to run in Python 3.

Running tweet_fetcher
---------------------

To run tweet_fetcher, first copy over tweet_fetcher from ./bin into ~/tedapp. Make sure that trigger_funcs.py has been copied from ./ted into ~/tedapp.

The config file for tweet_fetcher must exist in ~/tedapp and be named fetcher_config.ini. An example fetcher_config.ini can be found in this Git repository under ./exampleConfigFiles. The following pieces of information must be updated in the example fetcher_config.ini to use it with tweet_fetcher:

    db_ip                        IP address of the Postgres database
    db_port                      port number of the Postgres database
    db_name                      name of the Postgres database
    db_user                      username for the Postgres database
    db_password                  password for the Postgres database
    twitter_apikey               Twitter API account key
    twitter_apisecret            Twitter API account secret key
    twitter_accesstoken          Twitter API account token
    twitter_accesstoken_secret   Twitter API account secret token

Run tweet_fetcher as a background process by typing:

    python tweet_fetcher &
