detection_catcher_readme.md

Introduction
------------

Detection_catcher is an application which collects TED connections that come in from Kafka through Tomcat and writes them to a postgres database.

Installation and Dependencies
-----------------------------

The ted conda environment must be activated for whichever user is running PDL. To activate this environment, type:
    source activate ted
If the environment has not been created yet or does not exist, type:
    ./install.sh 

Detection_catcher requires that the detection_ext Postgres table exists. If this table has not been created, first activate the PostgreSQL Test_DB from the terminal by typing:

    psql -d <testDB_name> -U <testDB_user> -p <testDB_port>

And entering the same password that is used for the TED Dev database.
Create the detection_ext table by typing:

    create table detection_ext(
        detection_id bigint not null,
        detection_lat numeric(8,5),
        detection_lon numeric(8,5),
        detection_time timestamp without time zone,
        first_trigger_time timestamp without time zone
    );


Detection_catcher has been designed to run in Python 3.

Running detection_catcher.py
------------------------

Finish
