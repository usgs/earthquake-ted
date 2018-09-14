#!/usr/bin/env python

""" test_trigger_funcs.py - Tests functions in ../ted/trigger_funcs.py for the desired outputs.
"""

from ted.trigger_funcs import get_region_name
 
def test_get_region_name():
    """
    Test that the correct short version of the FE region name is 
    being returned for a given lat lon pair.
    """
    latitude = 33.6730
    longitude = -116.9448
    locstr = get_region_name(latitude, longitude)
    assert (locstr=='Southern California'), "Returned incorrect string!"

    latitude = 61.7281
    longitude = -148.6476
    locstr = get_region_name(latitude, longitude)
    assert (locstr=='Southern Alaska'), "Returned incorrect string!"

    latitude = 61.7281
    longitude = -648.6476
    locstr = get_region_name(latitude, longitude)
    assert (locstr == '%.3f, %.3f' % (latitude, longitude)), \
            "Returned incorrect string!"

    return("Correct string returned.")

if __name__ == '__main__':
    print(test_get_region_name())

