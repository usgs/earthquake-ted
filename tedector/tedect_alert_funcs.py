#!/usr/bin/env python

import sys
import os.path
import time
import datetime
import codecs
import logging.handlers
import psycopg2
import subprocess
import unidecode
from collections import Counter

# local objects
from tedect_geocode_funcs import esri_geocode, esri_reverse_geocode, get_esri_token


"""
tedect_alert_funcs.py - Functions used in tedect to handle the creation
                        and dispatching of an alert (detection)
"""

#######################################################################
def get_top_three_words(triggering_tweets):

# gets the three words appearing most frequently in the GEOS entry
# across all triggering tweets

    # returns the following dict
    count_dict = {}
    count_dict['1st_word'] = ''
    count_dict['1st_count'] = ''
    count_dict['2nd_word'] = ''
    count_dict['2nd_count'] = ''
    count_dict['3rd_word'] = ''
    count_dict['3rd_count'] = ''

    # combine all the city (l3) entries
    combined_l3 = ''
    for item in triggering_tweets:
        if 'l3' in item.keys() and len(item['l3']) > 0:
            combined_l3 = combined_l3 + ' ' + item['l3']

    # clean text and convert to all lowercase
    for char in "-.,\n":
        combined_l3 = combined_l3.replace(char, ' ')
    combined_l3 = combined_l3.lower()

    # split up
    word_list = combined_l3.split()

    # initialize dict object
    d = {}

    # count number of times each word comes up in list of words (in dictionary)
    for word in word_list: 
        d[word] = d.get(word, 0) + 1

    # reverse the key and values so they can be sorted using tuples.
    word_freq = []
    for key, value in d.items():
        word_freq.append((value, key))

    # sort from highest to lowest
    word_freq.sort(reverse=True)

    # transfer results to dict and return
    count_dict['1st_word'] = word_freq[0][1]
    count_dict['1st_count'] = str(word_freq[0][0])
    count_dict['2nd_word'] = word_freq[1][1]
    count_dict['2nd_count'] = str(word_freq[1][0])
    count_dict['3rd_word'] = word_freq[2][1]
    count_dict['3rd_count'] = str(word_freq[2][0])

    return count_dict


#######################################################################
def estimate_region(triggering_tweets):

#    scans the triggering tweets to locate the best estimate for the
#    location of the EQ.

    # returns the following dict
    estimate_dict = {}
    estimate_dict['most_common'] = False
    estimate_dict['ratio'] = False
 
    # define minimum match count
    match_count = 3

    # get the number of entries in the triggering_tweets list that
    # have been geocoded
    num_entries = 0
    for item in triggering_tweets:
        if 'GEOS' in item.keys() and len(item['GEOS']) > 0:
            num_entries += 1

    # build the dicts for the 3 levels
    l0_combined = {}      # country
    l1_combined = {}      # state or region
    l3_combined = {}      # city
    for item in triggering_tweets:
        # see if enough components are there to do l3
        if 'l3' in item.keys() and len(item['l3']) > 0:
            key = ''
            # if there's a state/region (l1), use it
            if 'l1' in item.keys() and len(item['l1']) > 0:
                key = item['l3'] + ', ' + item['l1'] + ', ' + item['l0']
            else:
                # no state/region, use city, country
                key = item['l3'] + ', ' + item['l0']
            l3_combined[key] = l3_combined.get(key, 0) + 1
        # see if enough components are there to do l1
        if 'l1' in item.keys() and len(item['l1']) > 0:
            key = item['l1'] + ', ' + item['l0']
            l1_combined[key] = l1_combined.get(key, 0) + 1
        # see if enough components are there to do l0
        if 'l0' in item.keys() and len(item['l0']) > 0:
            key = item['l0']
            l0_combined[key] = l0_combined.get(key, 0) + 1

    # start with l3, city
#    print('starting at l3, city')
    if len(l3_combined) > 0:
        #  copy to list (reversing key and value) and then sort
        l3_freq = []
        for key, value in l3_combined.items():
            l3_freq.append((value, key))
        l3_freq.sort(reverse=True)

        # use it if there are enough matches
        if l3_freq[0][0] >= match_count:
#            print('We got it! - l3')
            estimate_dict['most_common'] = l3_freq[0][1]
            estimate_dict['ratio'] = '(' + str(l3_freq[0][0]) + '/' + str(num_entries) + ')'
            return estimate_dict

    # if l3 fails, move to l1, state
#    print('working on l1, state')
    if len(l1_combined) > 0:
        #  copy to list (reversing key and value) and then sort
        l1_freq = []
        for key, value in l1_combined.items():
            l1_freq.append((value, key))
        l1_freq.sort(reverse=True)

        # use if there are enough matches
        if l1_freq[0][0] >= match_count:
#            print('We got it! - l1')
            estimate_dict['most_common'] = l1_freq[0][1]
            estimate_dict['ratio'] = '(' + str(l1_freq[0][0]) + '/' + str(num_entries) + ')'
            return estimate_dict

    # if l1 fails, move to l0, country
#    print('working on l0, country')
    if len(l0_combined) > 0:
        #  copy to list (reversing key and value) and then sort
        l0_freq = []
        for key, value in l0_combined.items():
            l0_freq.append((value, key))
        l0_freq.sort(reverse=True)

        # use if there are enough matches
        if l0_freq[0][0] >= match_count:
#            print('We got it! - l0')
            estimate_dict['most_common'] = l0_freq[0][1]
            estimate_dict['ratio'] = '(' + str(l0_freq[0][0]) + '/' + str(num_entries) + ')'
            return estimate_dict

    return estimate_dict


#######################################################################
def geocode_tweets(conn, access_token, tweet_list):
    # returns a dict list containing geocode info

    # initialize the list that will be returned
    dict_list = []

    for item in tweet_list:
        trigger_dict = {}
        trigger_dict['TIME'] = item['twitter_date']
        trigger_dict['UL'] = 'No location string'
        trigger_dict['GEO'] = 'None'
        trigger_dict['TXT'] = item['text']
        if item['location_string'] != 'No location string':
            trigger_dict['UL'] = item['location_string']
            # time to geocode
            if item['location_type'] == 'Location-String':
                geocode_dict = esri_geocode(conn, access_token,
                                            item['location_string'])
                if int(geocode_dict['qual']) >= 10:
                    trigger_dict['GEOS'] = geocode_dict['geos']
                    trigger_dict['GEO'] = str(geocode_dict['lat']) + ', ' + str(geocode_dict['lon']) + ' (C)'
                    trigger_dict['l3'] = geocode_dict['l3']
                    trigger_dict['l1'] = geocode_dict['l1']
                    trigger_dict['l0'] = geocode_dict['l0']
                    trigger_dict['lat'] = geocode_dict['lat']
                    trigger_dict['lon'] = geocode_dict['lon']
            elif item['location_type'] == 'GeoLocation':
                # when the location type is GeoLocation reverse_geocode it
                lat_lon = str(trigger_dict['lat']) + ',' + str(trigger_dict['lon'])
                geocode_dict = esri_reverse_geocode(conn, access_token, lat_lon)
                if int(geocode_dict['qual']) >= 10:
                    trigger_dict['GEOS'] = geocode_dict['geos']
                    trigger_dict['GEO'] = str(geocode_dict['lat']) + ', ' + str(geocode_dict['lon']) + ' (A)'
                    trigger_dict['l3'] = geocode_dict['l3']
                    trigger_dict['l1'] = geocode_dict['l1']
                    trigger_dict['l0'] = geocode_dict['l0']
            dict_list.append(trigger_dict)

    return dict_list


#######################################################################
def get_tweets (conn, trigger_time_str, logger, max_words,
                    filter_terms, sta_length):

    # returns two lists tweet dict dict objects - one for tweets
    # involved in triggering, and one for the others
    trig_dict_list = []
    other_dict_list = []

    # create a cursor object
    my_cur = conn.cursor()

    # convert sta_length from minutes to seconds
    window_duration = sta_length * 60

    # the end time of the tweet window is the trigger_time_str
    end_time = datetime.datetime.strptime(trigger_time_str, "%Y-%m-%d %H:%M:%S")
    end_time_str = trigger_time_str

    # convert end_time_str into datetime
    end_time = datetime.datetime.strptime(trigger_time_str, "%Y-%m-%d %H:%M:%S")

    # the start time is 60 seconds prior to the end time
    # to 60 seconds prior to that (i.e. a one minute window)
    start_time = end_time - datetime.timedelta(seconds=window_duration)
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    query = ("SELECT twitter_id,"                                          \
             " date_created,"                                              \
             " twitter_date,"                                              \
             " text,"                                                      \
             " to_be_geo_located,"                                         \
             " coalesce(st_y(message.location), 999) as lat,"              \
             " st_x(message.location) as lon,"                             \
             " coalesce(location_string, 'None'),"                         \
             " location_type"                                              \
             " FROM message"                                               \
             " WHERE twitter_date >= to_timestamp('"                       \
             + start_time_str + "', 'YYYY-MM-DD HH24:MI:SS')::timestamp"   \
             " AND twitter_date <= to_timestamp('"                         \
             + end_time_str + "', 'YYYY-MM-DD HH24:MI:SS')::timestamp"     \
             " ORDER BY id DESC;")
#    print('query: ' + query)

    try:
        my_cur.execute(query)
    except Exception as e:
        log_msg = ("SQL Error {} on {}")
        log_msg = log_msg.format(e, query)
        print(log_msg)
        logger.error(log_msg, exc_info=True)
        sys.exit(1)

    my_cur.execute(query)
    results = my_cur.fetchall()
    for row in results:
        tweet_dict = {}
        # process according to whether the tweet was used in a
        # trigger or not
        # the criteria for triggering tweets is that max_words
        # is satisfied and no filter term is present in the text
        # 1st, determine num_words - use unidecode to remove
        # emoji/emoticons from txt (they aren't words and shouldn't
        # be included in the count
        my_text = unidecode.unidecode(row[3])
        my_text = my_text.strip()
        my_words = my_text.split(' ')
        num_words = len(my_words)

        # scan the text to see if a filter term is there
        has_filter_term = False
        for my_word in filter_terms.split('|'):
            if my_word in my_text:
                has_filter_term = True
                break

        # now have enough info to process
        # the structure of trig_dict_list and other_dict_list differs,
        # but these elements are in both
        twitter_date = row[2]
        twitter_text = row[3]
        if row[7] is not None:
            ul = row[7]
        else:
            ul = 'No location string'
            # identify triggering tweets - In addition to the max_words
            # and filter terms criteria, the location_string has to be there
            # to be there
        if num_words <= max_words and has_filter_term is False and ul != 'No location string':
            tweet_dict['twitter_date'] = twitter_date
            tweet_dict['text'] = twitter_text
            tweet_dict['num_words'] = num_words
            tweet_dict['lat'] = row[5]
            tweet_dict['lon'] = row[6]
            tweet_dict['location_string'] = ul
            tweet_dict['location_type'] = row[8]
            trig_dict_list.append(tweet_dict)
        else:
            # this tweet is other
            tweet_dict['TIME'] = twitter_date
            tweet_dict['UL'] = ul
            tweet_dict['TXT'] = twitter_text
            other_dict_list.append(tweet_dict)



    # close the cursor object and return
    my_cur.close()

    return trig_dict_list, other_dict_list


#######################################################################

def alert(conn, trigger_time_str, logger, mail_dict,
          esri_dict, filter_terms, max_words, sta_length):

    log_msg = 'Preparing alert email notification for event triggered: {}'
    log_msg = log_msg.format(trigger_time_str)
    logger.info(log_msg)


    # get the tweets from the db for the time interval in question
    trigger_tweets, other_tweets = get_tweets(conn, trigger_time_str, logger,
                                max_words, filter_terms, sta_length)

    log_msg = '\tRetrieved {} triggering tweets and {} other tweets'
    log_msg = log_msg.format(len(trigger_tweets), len(other_tweets))
    logger.info(log_msg)

    if not trigger_tweets:
        print('trigger_tweets list is empty')
        return

    # get the esri access token
    access_token = get_esri_token(esri_dict)
    if access_token is None:
        print('def alert - could not get access token - cannot proceed')
        return

    # extract and geocode the triggering tweets
    geocoded_tweets = geocode_tweets(conn,
                                     access_token,
                                     trigger_tweets)
    log_msg = '\tGeocoded {} triggering tweets'
    log_msg = log_msg.format(len(geocoded_tweets))
    logger.info(log_msg)

#    for item in geocoded_tweets:
#        print('------------')
#        for key in item:
#            print('trig[' + key + ']: ' + str(item[key]))
#        sys.stdout.flush()
     
    # scan through geocoded_tweets to locate the best estimate for
    # the region
    region_estimate_dict = estimate_region(geocoded_tweets)

    # if region can be estimated, geocode it to get supplemental info
    subject_location = 'Location undetermined'
    have_region = False
    if region_estimate_dict['most_common']:
        subject_location = region_estimate_dict['most_common'] + ' ' + region_estimate_dict['ratio']
        geo_dict = esri_geocode(conn, access_token, region_estimate_dict['most_common'])
        top3_dict = get_top_three_words(geocoded_tweets)
        have_region = True

    log_msg = '\tEstimated location:'
    log_msg = log_msg.format(subject_location)
    logger.info(log_msg)

    # assign email file spec
    timestamp = trigger_time_str.replace(' ', '_')
    timestamp = timestamp.replace(':', '-')
    email_filespec = 'email' + timestamp + '.txt'

    # reformat the detection time to match the perl-based software
    detection_time = trigger_time_str.replace('-', '/')

    # make the subject line for the email
    subject = subject_location + ' ' + detection_time + ' ' + mail_dict['subject_tag']

    # make the email file
    with open(email_filespec, 'w+', encoding='utf-8') as f:
        f.write('Subject: ' + subject + '\n')
        f.write('From: ' + mail_dict['from'] + '\n')
        f.write('Twitter event detection\n')
        f.write('NOT AN OFFICIAL USGS ALERT\n')
        f.write('NOT SEISMICALLY VERIFIED\n')
        f.write('\n-------------\n')
        f.write('Detection Time: ' + '\n')
        f.write('-------------\n\n')
        f.write(detection_time + '\n\n')
        f.write('-------------\n')
        f.write('Possibly felt in:\n')
        f.write('-------------\n\n')
        if have_region:
            f.write(subject_location + '\n')
            f.write(geo_dict['lat'] + ', ' + geo_dict['lon'] + '\n')
            f.write('\n')
            f.write('City: ' + geo_dict['l3'] + '\n')
            f.write('Level1: ' + geo_dict['l1'] + '\n')
            f.write('Country: ' + geo_dict['l0'] + '\n')
            f.write('\n')
            f.write(top3_dict['1st_word'] + '  ' + top3_dict['1st_count'] + '\n')
            f.write(top3_dict['2nd_word'] + '  ' + top3_dict['2nd_count'] + '\n')
            f.write(top3_dict['3rd_word'] + '  ' + top3_dict['3rd_count'] + '\n')
            f.write('\n')
        else:
            f.write('Not enough for a good estimate.' + '\n')
        f.write('-------------\n')
        f.write('Triggering Tweets' + '\n')
        f.write('-------------\n\n')
        for item in geocoded_tweets:
            tweet_time = item['TIME'].strftime("%Y/%m/%d %H:%M:%S")
            f.write(tweet_time + '\n')
            if 'UL' in item.keys() and len(item['UL']) > 0:
                ul = item['UL']
                f.write('UL: ' + ul + '\n')
            if 'GEO' in item.keys() and len(item['GEO']) > 0:
                geo = item['GEO']
                f.write('GEO: ' + geo + '\n')
            if 'GEOS' in item.keys() and len(item['GEOS']) > 0:
                f.write('GEOS: ' + item['GEOS'] + '\n')
            if 'TXT' in item.keys() and len(item['TXT']) > 0:
                txt = item['TXT']
                f.write('TXT: ' + txt + '\n')
            f.write('\n')
        if len(other_tweets) > 0:
            f.write('-------------\n')
            f.write('Other Tweets' + '\n')
            f.write('-------------\n\n')
            for item in other_tweets:
                tweet_time = item['TIME'].strftime("%Y/%m/%d %H:%M:%S")
                f.write(tweet_time + '\n')
                ul = item['UL']
                f.write('UL: ' + ul + '\n')
                txt = item['TXT']
                f.write('TXT: ' + txt + '\n')
                f.write('\n')

        f.write("\n")
        f.write("-------------\n")
        f.write("Information on recent earthquakes\n")
        f.write("-------------\n\n")
        f.write("USGS: http://on.doi.gov/2IZXwx\n")
        f.write("EMSC: http://bit.ly/gGYick\n")
        f.write("U Chile: http://www.sismologia.cl\n")
        f.write("Japan: http://bit.ly/gE1CwL\n")
        f.write("Indonesia: http://bit.ly/AiQfCl\n")
        f.write("New Zealand: http://bit.ly/yWaMsK\n")
        f.write("\n")
        f.write("-------------\n")
        f.write("Background:\n")
        f.write("-------------\n\n")
        f.write("This possible earthquake detection is based solely on Twitter data and has not been seismically verified. We use a sensitive trigger so expect some false triggers. The first tweets listed generally precede tweets about the event and are from random locations around the world. False triggers can usually be identified by scanning the the tweet text to see if it is consistent with what you would expect after an earthquake. False triggers often contain repeat text or tweets that all come from random locations around the globe.\n\n")
        f.write("Detection Time:\nThe detection time is usually 1 to 5 minutes after earthquake origin time. Earthquakes are generally detected before seismically derived solutions are publicly available.\n\n")
        f.write("Location Estimate:\nThe location estimate is our best estimate of city that produced the most tweets. This is followed by the most common words with counts in the user's location string.\n\n")
        f.write("Tweets:\nFor each tweet we may list:\n")
        f.write("1) UTC time that the tweet was sent\n")
        f.write("2) User provided location string (UL:)\n")
        f.write("3) Best guess of user coordinates (GEO:)\n")
        f.write("4) Geolocation string returned from ArcGIS World Geocoding Service (GEOS:)\n")
        f.write("5) Tweet text (TXT:)\n")
        f.write("All tweets shown starting one minute prior to detection time\n\n")
        f.write("Location details:\n")
        f.write("UL: Corresponds to the user supplied free-format text string. This can be inaccurate because users often enter \"clever\" locations such as \"on the earth\". Additionally, they may not be in their home city when they sent the tweet. Some twitter clients insert a decimal latitude and longitude in the location string.\n\n")
        f.write("GEO: Corresponds to our best estimate of the latitude and longitude.\n")
        f.write("The source of the geolocation is indicated by a letter following the latitude and longitude:\n")
        f.write("(A) a precise latitude and longitude, likely GPS based.\n")
        f.write("(B) A Twitter \"place\" location, usually accurate to the city level.\n")
        f.write("(C) a geolocation of the users free-format location string (UL). This is only as good as what the user specifies in the free-format location string and what the ArcGIS geocode service returns. Some locations may not have been geocoded at the time the alert was sent.\n")
        f.write("\n\n")

    f.close()

    # send the alert email
    command = '/usr/sbin/sendmail ' + mail_dict['detection_list'] + ' < ' + email_filespec
    subproc = subprocess.Popen([command], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    (out, err) = subproc.communicate(timeout=10)    # waits for child proc
    out = out.decode("utf-8")
    out = str(out)

    log_msg = '\tAlert emailed'
    log_msg = log_msg.format(subject_location)
    logger.info(log_msg)

    return
