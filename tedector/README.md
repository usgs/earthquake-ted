# Introduction: Tweet Earthquake Detection source code repository

tedect is a Python application designed to implement the algorithm described in the publication named "Twitter earthquake detection: earthquake monitoring in a social world" which is located online at https://www.annalsofgeophysics.eu/index.php/annals/article/viewFile/5364/5494

# Dependencies

The dependencies that must be satisified to run tedect are:
  - Python
  - ESRI account for access to the ArgGIS World Geocoding Service
  - Twitter2Pg installed, running, and loading a postgres database

## Python

tedect was developed using the Miniconda distribution of Python 3.6.  We recommend using either the Miniconda (https://conda.io/miniconda.html) or Anaconda (https://www.anaconda.com/) distributi
ons.  Both use the 'conda' packaging tool, which makes installation of dependencies much simpler.  A file named environment.yml is provided in order to set up a custom conda environment to satisfy the package dependencies.

## ESRI geocoding web service 


Documentation:
https://developers.arcgis.com/rest/geocode/api-reference/overview-world-geocoding-service.htm 

Return results/fields documentation
https://developers.arcgis.com/rest/geocode/api-reference/geocoding-service-output.htm

Authentication:
The authentication user id and secret access token go in the tedect configuration file (tedect.ini) - see below


## Twitter2Pg

See https://github.com/usgs/earthquake-ted/tree/master/Twitter2Pg


# Installation

1. Install and configure Python (Miniconda or Anaconda are preferred)

2. Install Twitter2Pg
   git clone https://github.com/usgs/earthquake-ted
   (note: The Twitter2Pg app is in the directory of the same name)

# Configuration

1. create conda environment
  a. cd to the tedector directory
  b. run the following command to create a custom conda environment named TEDECT
    conda env create -f environment.yml
  c. add the following line to the bottom of ~/.bashrc
    source activate TEDECT

2. configure tedect
  a. the configuration file is named tedect.ini, located in the tedector directory
  b. optional: alter the settings in the [SETUP] section
  c. required: edit the [DATABASE] section.  The value of the 'name' keyword is whatever was used in the 'your-database' part of the CREATE DATABASE statement.  The value of the 'user' and 'password
 keywords is whatever was used in the 'your-role' and 'your-password' part of the CREATE ROLE statement.
  d. required: edit the [ESRI] section to provide the values for the set of tokens for the ESRI World Geocoding Service
  e. required: edit the [MAIL] section to set the 'from', 'subject_tag' and 'detection_list' variables accoringly




    
