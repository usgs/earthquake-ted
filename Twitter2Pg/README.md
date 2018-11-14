# Introduction

Twitter2Pg is a Python application designed to connect to the Twitter streaming API using a filter containing Twitter filter terms stored in a database table named 'keywords'.  Once connected, the application reads messages (tweets) from the stream.  For each message received, additional filtering is performed to eliminate unwanted tweets (filtering is done via entries in the configuration file).  Messages passing all filter tests are stored in a database table named 'messages.'  Note that the information stored is only a portion of the full tweet.

# Dependencies

The dependencies that must be satisified to run Twitter2Pg are:
  - Python
  - Twitter account
  - postgresSQL database propertly configured (shown below)


## Python

Twitter2Pg was developed using the Miniconda distribution of Python 3.6.  We recommend using either the Miniconda (https://conda.io/miniconda.html) or Anaconda (https://www.anaconda.com/) distributions.  Both use the 'conda' packaging tool, which makes installation of dependencies much simpler.  A file named environment.yml is provided in order to set up a custom conda environment to satisfy the package dependencies.


## Twitter

Twitter2Pg requires an authorized Twitter developer account with the following:
- api key
- api secret
- access token
- access token secret

# Installation

1. Install and configure Python (Miniconda or Anaconda are preferred)

2. Install Twitter2Pg
   git clone https://github.com/usgs/earthquake-ted
   (note: The Twitter2Pg app is in the directory of the same name)


# Configuration

1. create conda environment
  a. cd to the Twitter2Pg directory
  b. run the following command to create a custom conda environment named TED
    conda env create -f environment.yml
  c. add the following line to the bottom of ~/.bashrc
    source activate TED

2. Setup postgreSQL
  a. install postgres 9.6 or higher
  b. follow documentation steps at https://www.postgresql.org to initialize the database
  c. connect as the postgres (root) user and issue the following SQL commands (note: -- is a comment in postgres)
    -- create a role to own the database (replace your-role and your-password as appropriate)
    CREATE ROLE your-role LOGIN UNENCRYPTED PASSWORD 'your-password' NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;
    -- create a database
    CREATE DATABASE your-database WITH OWNER = your_role ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8' CONNECTION LIMIT = -1;
    -- create the 'keyword' table
    CREATE TABLE public.keyword (
      id bigint NOT NULL,
      version bigint NOT NULL,
      title character varying(60) NOT NULL,
      CONSTRAINT keyword_pkey PRIMARY KEY (id)
    )
    WITH (
      OIDS=FALSE
    );
   ALTER TABLE public.keyword OWNER TO your-role;
   GRANT ALL ON TABLE public.keyword TO your-role;
   -- create the 'message' table
   CREATE TABLE public.message (
     id bigint NOT NULL DEFAULT nextval('message_id_seq'::regclass),
     date_created timestamp without time zone NOT NULL,
     twitter_id bigint NOT NULL,
     twitter_date timestamp without time zone NOT NULL,
     to_be_geo_located boolean NOT NULL,
     text character varying(280) NOT NULL,
     location_string character varying(255),
     opt_location_string character varying(255),
     orig_location_string character varying(255),
     location_type character varying(40),
     location geometry,
     in_reply_to_message_id bigint,
     lang character varying(5),
     media_display_url character varying(255),
     media_type character varying(40),
     time_zone character varying(255),
     CONSTRAINT message_pkey PRIMARY KEY (id),
     CONSTRAINT enforce_dims_location CHECK (st_ndims(location) = 2),
     CONSTRAINT enforce_geotype_location CHECK (geometrytype(location) = 'POINT'::text OR location IS NULL),
     CONSTRAINT enforce_srid_location CHECK (st_srid(location) = 4326)
   )
   WITH (
     OIDS=FALSE
   );
   ALTER TABLE public.message OWNER TO your-role;
   GRANT ALL ON TABLE public.message TO your-role;
   CREATE INDEX message_twitter_date_idx
     ON public.message
     USING btree
     (twitter_date);

3. configure Twitter2Pg
  a. the configuration file is named Twitter2Pg.ini, located in the Twitter2Pg directory
  b. optional: alter the settings in the [SETUP] section
  c. required: edit the [DATABASE] section.  The value of the 'name' keyword is whatever was used in the 'your-database' part of the CREATE DATABASE statement.  The value of the 'user' and 'password keywords is whatever was used in the 'your-role' and 'your-password' part of the CREATE ROLE statement.
  d. required: edit the [TWITTER] section to provide the values for the set of tokens for the Twitter developer account
  e. optional: edit the [TWITTER] section to modify values for other keys in this seciton.  See the comments in the configuration file for more details

# Running Twitter2Pg
1.  Edit the checkTwitter2Pg.sh script to change the COMMAND assignment to reflect the full path for the application, then run with checkTwitter2Pg.sh the start option.  It is recommended to put a call to this script with the restart option in the crontab running every 5 minutes.
