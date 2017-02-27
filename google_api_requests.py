# Script to send API requests to Google API's
import requests

# Constants
GOOGLE_API_KEY = 'YOUR KEY HERE'
GOOGLE_PLACES_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'

def get_coordinates(place_name, user):
    # Package params into dictionary for GET request (Ref: https://developers.google.com/places/web-service/search#PlaceSearchResponses)
    params = {
        'key':GOOGLE_API_KEY,
        'query':place_name,
        'location':str(user.start_lat) + ',' + str(user.start_lng),
        'radius':35000
    }

    # Send GET request to Google.
    r = requests.get(GOOGLE_PLACES_URL, params=params)

    try:
        end_lat = r.json()['results'][0]['geometry']['location']['lat']
        end_lng = r.json()['results'][0]['geometry']['location']['lng']
    except:
        # If request didn't work or there was no results, send error coordinate back.
        return (0,0)

    # Return end coordinates in a tuple
    return (end_lat, end_lng)
