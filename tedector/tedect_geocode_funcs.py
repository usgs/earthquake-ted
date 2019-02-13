#!/usr/bin/env python

import codecs
import psycopg2
import json
import requests
import unidecode

####################
def state_table_lookup(conn, region):

    # create a cursor object
    my_cur = conn.cursor()

    # returns state, state_abbrev, state_aliases
    state = ''
    state_abbrev = ''
    state_aliases = ''

    if region is not None:
        state = region
        query = "SELECT state, code, aliases FROM states WHERE state='" + region + "'";

        try:
            my_cur.execute(query)
        except Exception as e:
            log_msg = ("get_state SQL Error {} on {}")
            log_msg = log_msg.format(e, query)
            print(log_msg)
            logger.error(log_msg, exc_info=True)
            sys.exit(1)

        row = my_cur.fetchone()
        if row is not None:
            state = row[0]
            state_abbrev = row[1]
            state_aliases = row[2]
        else:
            print('get_state failed for region = ' + region)

    # close the cursor object and return
    my_cur.close()
    return state, state_abbrev, state_aliases


####################
def get_country_common_name_and_aliases(conn, country):

    # create a cursor object
    my_cur = conn.cursor()

    # these two will be returned
    country_common_name = country
    country_aliases = ''

    # ESRI returns abbreviated country, which is not that
    # useful.  Query the countries table to get common_name and aliases
    query = "SELECT common_name, aliases FROM countries WHERE code='" + country + "'";

    try:
        my_cur.execute(query)
    except Exception as e:
        log_msg = ("process_country SQL Error {} on {}")
        log_msg = log_msg.format(e, query)
        print(log_msg)
        logger.error(log_msg, exc_info=True)
        sys.exit(1)

    row = my_cur.fetchone()
    if row is not None:
        country_common_name = row[0]
        if row[1] is not None:
            country_aliases = row[1]

    # close the cursor object and return
    my_cur.close()
    return country_common_name, country_aliases


####################
def get_esri_response(token, location):

    data_response = None

    # build address table to send to geocoding service
    address = '{ "records": [';
    address = address + '{"attributes":{"OBJECTID":1,"SingleLine":"' + location + '"}}]}';

    # create the data URL
    data_url = 'http://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/geocodeAddresses?addresses=' + address + '&token=' + token +'&f=pjson';
#    print('data_url: ' + data_url)

    got_response = False
    for i in range(1, 5):
        # get the result
        try:
            data_response = requests.get(data_url, timeout=5)
            # Consider any status other than 2xx an error
            if not data_response.status_code // 100 == 2:
                err_msg = "ERROR: Unexpected response {}".format(response)
                print(err_msg)
                print('status_code: ' + str(data_response.status_code // 100))
                data_response = None
            else:
                got_resonse = True
        except requests.exceptions.RequestException as e:
            # A serious problem happened, like an SSLError or InvalidURL
            print("get_esri_response Error: {}".format(e))
            print('except status_code: ' + str(data_response.status_code // 100))
            data_response = None
        if got_resonse:
            break
        else:
            print('failed to get esri response, try again (' + str(i))
    return data_response


###########i#########
def get_esri_token(esri_dict):

    accesss_token = None
    # extract/cleanup ESRI credentials
    clientId = esri_dict['clientId'].strip()
    clientSecret = esri_dict['clientSecret'].strip()

    # get OAuth 2.0 token from ArcGIS
    auth_url = "https://www.arcgis.com/sharing/oauth2/token?" + \
                "client_id=" + clientId                       + \
                "&grant_type=client_credentials&"             + \
                "client_secret=" + clientSecret               + \
                "&f=pjson"

    try:
        token_response = requests.get(auth_url, timeout=5)
        # Consider any status other than 2xx an error
        if not token_response.status_code // 100 == 2:
            err_msg = "Error: Unexpected response {}".format(response)
            print(err_msg)
            return result_loc
        json_token_response = token_response.json()
        access_token =  json_token_response['access_token']
    except requests.exceptions.RequestException as e:
        # A serious problem happened, like an SSLError or InvalidURL
        print("get_esri_token Error: {}".format(e))

    return access_token


####################
def clean_location_string(location_string):

    # replace odd characters (esp. diacritical marks)
    clean_loc = unidecode.unidecode(location_string)

    # remove non-ascii characters
    clean_loc = clean_loc.encode('ascii',errors='ignore')
    clean_loc = clean_loc.decode("utf-8")

    # remove whitespace from both ends
    clean_loc = clean_loc.strip()

    # eliminate ampersands, question marks, quotation marks,
    # parentheses, dashes and hash marks
    clean_loc = clean_loc.replace('&', ' ')
    clean_loc = clean_loc.replace('?', ' ')
    clean_loc = clean_loc.replace('"', ' ')
    clean_loc = clean_loc.replace("'", ' ')
    clean_loc = clean_loc.replace('(', ' ')
    clean_loc = clean_loc.replace(')', ' ')
    clean_loc = clean_loc.replace('-', ' ')
    clean_loc = clean_loc.replace('#', ' ')

    # eliminate forward and back slash marks
    clean_loc = clean_loc.replace('/', ' ')
    clean_loc = clean_loc.replace('\\', ' ')

    # eliminate periods
    clean_loc = clean_loc.replace('.', ' ')

    # eliminate line breaks
    clean_loc = clean_loc.replace('\n', ' ')

    # eliminate multiple spaces
    while '  ' in clean_loc:
        clean_loc = clean_loc.replace('  ', ' ')

    return clean_loc


####################
def esri_geocode(conn, access_token, target_loc):

    # the return is a dict for the result location
    # initialize it
    result_loc = {}
    result_loc['loc_string'] = target_loc
    result_loc['lat'] = 999;
    result_loc['lon'] = 999;
    result_loc['qual'] = 0;
    result_loc['l0'] = "";
    result_loc['l1'] = "";
    result_loc['l2'] = "";
    result_loc['l3'] = "";
    result_loc['geos'] = "";

    # replace odd characters (esp. diacritical marks)
    clean_target_loc = clean_location_string(target_loc)

#    print('----------------')
#    print('esri_geocode clean_target_loc: [' + str(clean_target_loc) + ']')

    # if sting is empty, just return
    if not clean_target_loc:
        return result_loc

    # get the result from ESRI world geocoding service
    data_response = get_esri_response(access_token, clean_target_loc)
    if data_response is None:
        print('esri_geocode - could not get query response')
        return result_loc
    json_data_response = data_response.json()

    # extract the relevant items in the response
    esri_status = json_data_response['locations'][0]['attributes']['Status']
    esri_country = json_data_response['locations'][0]['attributes']['Country']

    # Cannot continue if Status = U or Country field is undefined
    if esri_status == "U" or esri_country is None:
        print('return is either unmatched or has no country')
        return result_loc

    # extract the relevant entries in the response
    esri_addr_type = json_data_response['locations'][0]['attributes']['Addr_type']
    esri_type = json_data_response['locations'][0]['attributes']['Type']
    esri_city = json_data_response['locations'][0]['attributes']['City']
    esri_metroArea = json_data_response['locations'][0]['attributes']['MetroArea']
    esri_region = json_data_response['locations'][0]['attributes']['Region']
#    esri_lat = str(round(json_data_response['locations'][0]['attributes']['Y'], 3))
#    esri_lon = str(round(json_data_response['locations'][0]['attributes']['X'], 3))
    esri_lat = json_data_response['locations'][0]['attributes']['Y']
    esri_lat = "{:.3f}".format(esri_lat)
    esri_lon = json_data_response['locations'][0]['attributes']['X']
    esri_lon = "{:.3f}".format(esri_lon)


    # replace odd (e.g diacriticals) characters
    esri_country = unidecode.unidecode(esri_country)
    esri_city = unidecode.unidecode(esri_city)
    esri_metroArea = unidecode.unidecode(esri_metroArea)
    esri_region = unidecode.unidecode(esri_region)

#    print('--------')
#    print('Status: ' + esri_status)
#    print('Addr_type: ' + esri_addr_type)
#    print('Type: ' + esri_type)
#    print('City: ' + esri_city)
#    print('MetroArea: ' + esri_metroArea)
#    print('Region: ' + esri_region)
#    print('Country: ' + esri_country)
#    print('lat: ' + esri_lat)
#    print('lon: ' + esri_lon) 
#    print()

    # initilaze the TED analogs of the esri fields (these
    # may be altered downstream
    TED_country = esri_country
    TED_city = esri_city
    TED_state_or_region = ''
    TED_state = ''
    TED_quality = 0
    why = ''

    # these booleans are used in quality assignment
    country_match = False
    city_match = False
    state_or_region_match = False

    # the following logic involves searching for ESRI's
    # address components (Country, Region/State, City) in the
    # original location_string, but the original string must
    # must be prepared for searching(word matching) by
    # replacing commas with spaces, converting to lower case,
    # and adding a space to beginning and end
    orig_loc = clean_target_loc.lower()
    orig_loc = orig_loc.replace(',', ' ')
    orig_loc = ' ' + orig_loc + ' '

    # translate the esri_country to get a better version and obtain
    # any aliases (if defined)
    TED_country, country_aliases = get_country_common_name_and_aliases(conn, esri_country)

    # sometimes the Region and common name for Country are the same
    # must correct in order not to count or list twice
    if esri_region == TED_country or esri_region == esri_country:
        esri_egion = '';

    # if ESRI's return country (or any alias) is in the original
    # location string, set country_match to True
    # 1st, make a copy of country_common_name and prepare it for search
    name = TED_country.lower()
    name = name.strip()
    name = ' ' + name + ' '
    if name in orig_loc:
        country_match = True
    else:
        # if country_aliases exist, see if any of the aliases match a
        # word in the original location
        if len(country_aliases) > 0:
            # note: aliases is a comma-separated string of alternate spellings
            aliases = country_aliases.split(',')
            for alias in aliases:
                # convert to lower case
                alias = alias.lower()
                # strip extraneous whitespace on both ends
                alias = alias.strip()
                # add a space to beginning and end to turn it into
                # a word
                alias = ' ' + alias + ' '
                if alias in orig_loc:
                    country_match = True
                    break
#    print('Country processed')
#    print('\tTED_country: ' + TED_country)

    # process the City part of the response
    # Note: outside US, city might be in MetroArea or Region
    # scan items to get best candidate for city
    city_candidate = ''
    why = ''
    if len(esri_city) > 0:
        city_candidate = esri_city
    elif len(esri_metroArea) > 0:
        city_candidate = esri_metroArea
    elif len(esri_region) > 0:
        # for US responses, the Region is the state, and can't be used as city
        if TED_country != 'United States':
            city_candidate = esri_region;
    # if a candidate was found, see if it's in the original location
    if len(city_candidate) > 0:
        # set the City variable
        TED_city = city_candidate
        city = city_candidate.lower()
        city = city.strip()
        city = ' ' + city + ' '
        # remove parentheses (because they were removed from orig_loc)
        city = city.replace('(', '')
        city = city.replace(')', '')
        if city in orig_loc:
            # returned city is in original search string - set flag to true
            city_match = True
#    print('City processed')
#    print('\tTED_city: ' + TED_city)
#    print()

    # process state_or_region
    why = ''
    if TED_country == 'United States':
        # for responses in the US, the State is in esri_region
        # for locations in the US, get and translate the state using
        # the Region
        TED_state_or_region, state_abbrev, state_aliases = state_table_lookup(conn, esri_region)
        # see if TED_state is in search string
        state = TED_state_or_region
        state = state.lower()
        state = state.strip()
        state = ' ' + state + ' '
        if state in orig_loc:
            state_or_region_match = True
        else:
            # see if state_abbrev is in search string
            state_abbrev = state_abbrev.lower()
            state_abbrev = state_abbrev.strip()
            state_abbrev = ' ' + state_abbrev + ' '
            if state_abbrev in orig_loc:
                state_or_region_match = True
            else:
                if state_aliases is not None and len(state_aliases) > 0:
                    # see if any abbreviations are in search string
                    aliases = state_aliases.split(',')
                    for alias in aliases:
                        alias = alias.lower()
                        alias = alias.strip()
                        alias = ' ' + alias + ' '
                        if alias in orig_loc:
                            state_or_region_match = True
                            break
    else:
        # for responses outside USA, do region/state, but only if defined and
        # if region NOT used as city above and region isn't England
        if len(esri_region) > 0 and esri_region != TED_city and esri_region != 'England':
            TED_state_or_region = esri_region
            region = esri_region
            region = region.lower()
            region = region.strip()
            region = ' ' + region + ' '
            if region in orig_loc:
                state_or_region_match = True
            else:
                # there's an inconsistency with the use of '&' and 'and'
                # try to resolve it
                region = region.replace('&', ' ')
                region = region.replace('and', ' ')
                orig_loc_temp = orig_loc.replace('$', ' ')
                orig_loc_temp = orig_loc_temp.replace('and', ' ')
                if region in orig_loc_temp:
                    state_or_region_match = True
#    print('US state processed')
#    print('\tTED_state_or_region: ' + TED_state_or_region)
 
    # do final quality assignment
    # handle assignment separately for locations in US and elsewhere
    # NOTE: the caller should use any result with a quality >= 10
    if TED_country == 'United States':
        # rationale: lots of locations in the US have city and/or
        # state, but no country, so automatically start with
        # quality of 9 so match on city or state pushes
        # it to above 10
        TED_quality = 9
    elif country_match:
        TED_quality = 10

    if city_match:
        TED_quality += 4
    if state_or_region_match:
        TED_quality += 4

    # create geos string (full location, comma separated) but
    # keep it clean (no extraneous spaces or commas in beginning)
    TED_geos = ''
    if len(TED_country) > 0:
        TED_geos = TED_country
        if len(TED_state_or_region) > 0:
            TED_geos = TED_state_or_region + ', ' + TED_geos
        if len(TED_city) > 0:
            TED_geos = TED_city + ', ' + TED_geos

    result_loc['qual'] = str(TED_quality)
    result_loc['l0'] = TED_country
    result_loc['l1'] = TED_state_or_region
    result_loc['l3'] = TED_city
    result_loc['geos'] = TED_geos
    result_loc['lat'] = esri_lat;
    result_loc['lon'] = esri_lon;

#    print()
#    print('Final for ' + clean_target_loc)
#    print('\t     Quality: ' + result_loc['qual'])
#    print('\t        City: ' + result_loc['l3'])
#    print('\tState/Region: ' + result_loc['l1'])
#    print('\t     Country: ' + result_loc['l0'])
#    print('\t     lat/lon: ' + str(result_loc['lat']) + ', ' + str(result_loc['lon']))
#    print('\t        geos: ' + result_loc['geos'])

    return result_loc


####################
def esri_reverse_geocode(conn, access_token, location):
    # args: access_token, location (comma-separated lat,lon pair)
    # returns: result_loc dict (as in esri_geocode)

    # create and clear result_loc
    result_loc = {}
    result_loc['loc_string'] = ''
    result_loc['lat'] = 999;
    result_loc['lon'] = 999;
    result_loc['qual'] = 0;
    result_loc['l0'] = "";
    result_loc['l1'] = "";
    result_loc['l2'] = "";
    result_loc['l3'] = "";
    result_loc['geos'] = "";

    # get the lat and lon
    lat_lon = location.split(',')
    lat = lat_lon[0]
    lon = lat_lon[1]

    if lat is None or lon is None:
        print('esri_reverse_geocode - missing lat an/or lon')
        return result_loc
        
    # make the request and check the response code
    # build request to send to ArcGIS geocoding service
    data_url = 'http://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/reverseGeocode?location=' + lon + ',' + lat + '&token=' + access_token + '&langCode=EN&f=pjson';
#    print('esri_reverse_geocode data_url: ' + data_url)
    got_response = False
    for i in range(1, 5):
        # get the result
        try:
            data_response = requests.get(data_url, timeout=5)
            # Consider any status other than 2xx an error
            if not data_response.status_code // 100 == 2:
                err_msg = "ERROR: Unexpected response {}".format(response)
                print(err_msg)
                print('status_code: ' + str(data_response.status_code // 100))
                data_response = None
            else:
                got_resonse = True
        except requests.exceptions.RequestException as e:
            # A serious problem happened, like an SSLError or InvalidURL
            print("get_esri_response Error: {}".format(e))
            print('except status_code: ' + str(data_response.status_code // 100))
            data_response = None
        if got_resonse:
            break
        else:
            print('failed to get esri response, try again (' + str(i))

    #==============================
    json_data_response = data_response.json()

    # extract the relevant items in the response
    esri_country = json_data_response['address']['CountryCode']
    esri_city = json_data_response['address']['City']
    esri_region = json_data_response['address']['Region']

    # replace odd (e.g diacriticals) characters
    esri_country = unidecode.unidecode(esri_country)
    esri_city = unidecode.unidecode(esri_city)
    esri_region = unidecode.unidecode(esri_region)

    # initilaze the TED analogs of the esri fields (these
    # may be altered downstream
    TED_country = esri_country
    TED_city = esri_city
    TED_state_or_region = ''
    TED_state = ''
    TED_quality = 0
    TED_geos = ''

    # translate the esri_country to get a better version (but ignore aliases) and
    # up quality if successful
    TED_country, country_aliases = get_country_common_name_and_aliases(conn, esri_country)
    if TED_country is not None:
        TED_quality = TED_quality + 10

    # if the esri_region is defined, use it and up quality
    if esri_region is not None:
        TED_region = esri_region
        TED_quality = TED_quality + 10

    # if the esri_city is defined, use it and up quality
    if esri_city is not None:
        TED_cify = esri_city
        TED_quality = TED_quality + 10

    # create the geos string
    if len(TED_country) > 0:
        TED_geos = TED_country
        if len(TED_region) > 0:
            TED_geos = TED_region + ', ' + TED_geos
        if len(TED_city) > 0:
            TED_geos = TED_city + ', ' + TED_geos

    # populate result_loc
    result_loc['qual'] = str(TED_quality)
    result_loc['l0'] = TED_country
    result_loc['l1'] = TED_region
    result_loc['l3'] = TED_city
    result_loc['geos'] = TED_geos

    return result_loc

####################
