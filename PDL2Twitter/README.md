# Introduction

PDL2Twitter is a Python application designed to send Earthquake Event Notification tweets to one or more pre-existing Twitter accounts.

The USGS Product Distribution Layer (PDL @ https://github.com/usgs/pdl) invokes PDL2Twitter when earthquake products arrive, passing a set of earthquake event parameters on the command line.  If the parameters meet an established criteria, PDL2Twitter will send out Earthquake Event Notification tweets to up to four (4) Twitter accounts.

A postgres database is used to record sent tweets to prevent them from being sent more than one time, and to make a record of earthquake events.


# Dependencies

The dependencies that must be satisified to run PDL2Twitter are:
  - Python
  - USGS Product Distribution Layer (PDL)
  - Twitter account(s)
  - GoUSA account
  - postgresSQL database


## Python

PDL2Twitter was developed using the Miniconda distribution of Python 3.6.  We recommend using either the Miniconda (https://conda.io/miniconda.html) or Anaconda (https://www.anaconda.com/) distributions.  Both use the 'conda' packaging tool, which makes installation of dependencies much simpler.  A file named environment.yml is provided in order to set up a custom conda environment to satisfy the package dependencies.


## PDL

The USGS Product Distribution Layer (PDL) must be installed and configured.  Download and documentation are available at https://github.com/usgs/pdl


## Twitter

PDL2Twitter supports up to four (4) individual Twitter accounts.  At least one account is required. Each account has four tokens:
- api key
- api secret
- access token
- access token secret

See the PDL2Twitter Configuration Section for details


## GoUSA account

A GoUSA account is required, which will provide a username and gousa api key.



# Installation

1. Install and configure Python (Miniconda or Anaconda are preferred)

2. Install and configure PDL (if necessary)

3. Install PDL2Twitter
   git clone https://github.com/usgs/earthquake-ted


# Configuration

1. create conda environment
  a. cd to the Twitter2PDL directory
  b. run the following command to create a custom conda environment named TED
    conda env create -f environment.yml
  c. add the following line to the bottom of ~/.bashrc
    source activate TED

2. configure PDL
  a. the typical PDL installation puts all files in a directory named ProductClient
  b. cd to that directory or equivalent
  c. edit the config.ini as follows:
    - navigate to the [indexer_listener_exec] section and edit the 'command = ' line
      to specify the fully qualified name for the Twitter2PDL python file
      (e.g. command = /home/youraccount/earthquake-ted/PDL2Twitter/PDL2Twitter)

3. configure PDL2Twitter
  a. the configuration file is named PDL2Twitter.ini, which is located in the PDL2Twitter directory
  b. optional: alter the settings in the [SETUP] section
  c. required: edit the [GOUSA] section to identify the username and api key associated with the account
  d. required: edit the [DATABASE] section to provide the database name, user name, and password for postgreSQL
  e. required: edit the [TWITTER] section to provide at least one set of tokens for one of the accounts
  See the comments in the configuration file for more details

4. Setup postgreSQL
  a. A postgreSQL database is required, containing two tables that need to be in the same schema of a database. The following SQL statements will create those tables in the public schema of a database named ted.  Alter to suit the specifics of your database.

CREATE TABLE public.tweet_audit
(
  id BIGSERIAL NOT NULL,
  event_id character varying(40) NOT NULL,
  event_lat numeric(8,5),
  event_lon numeric(8,5),
  event_time timestamp without time zone,
  magnitude real,
  tweet_time timestamp without time zone NOT NULL,
  tweet_text character varying(290) NOT NULL,
  account_id character varying(50),
  CONSTRAINT tweet_audit_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);


CREATE TABLE public.event
(
  id BIGSERIAL NOT NULL,
  version bigint NOT NULL,
  date_created timestamp without time zone NOT NULL,
  depth real NOT NULL,
  event_id character varying(40) NOT NULL,
  event_time timestamp without time zone NOT NULL,
  last_updated timestamp without time zone NOT NULL,
  magnitude real NOT NULL,
  mini_uri character varying(255),
  network_code character varying(255) NOT NULL,
  region_name character varying(255) NOT NULL,
  uri character varying(255) NOT NULL,
  location geometry,
  population_from_grid double precision,
  population_fromwps double precision,
  CONSTRAINT event_pkey PRIMARY KEY (id),
  CONSTRAINT enforce_dims_location CHECK (st_ndims(location) = 2),
  CONSTRAINT enforce_geotype_location CHECK (geometrytype(location) = 'POINT'::text OR location IS NULL),
  CONSTRAINT enforce_srid_location CHECK (st_srid(location) = 4326)
)
WITH (
  OIDS=FALSE
);

CREATE INDEX event_loc_idx
  ON public.event
  USING gist
  (location);


# Running PDL2Twitter

Whenever PDL gets an Earthquake Event product it will invoke PDL2Twitter.  Once PDL is configured and running, and PDL2Twitter is configured, check the log files to confirm the software is running correctly.
