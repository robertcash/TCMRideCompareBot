# Script to send messages to FB Messenger via FB Messenger Send API
import requests

# Constants
FB_ACCESS_TOKEN = 'EAAI3PTX0WzgBAJnsZBoZAUVcRWaMvsvrb3SDHZBW1A3wpRZAKZAtGpUhUXXZC3ORJv7FEkxq9M96oBewhQ1Dj9xiHNEphZBvkayInhZBsxSPZBkDHR1bjldfE8OuUHzq2bECxis5jikNkvx0TTnxnNm0wlyALVM64QzdgqU9oxSFbeQZDZD'
SEND_API_URL = 'https://graph.facebook.com/v2.6/me/messages?access_token=' + FB_ACCESS_TOKEN

def send_message(messenger_id, text):
    # Package params into dictionaries for POST request
    recipient = {'id':messenger_id}
    message = {'text':text}
    params = {
        'recipient':recipient,
        'message':message
    }

    # Send POST request to Facebook Messenger Send API to send text message
    r = requests.post(SEND_API_URL, json=params)

def send_coordinates_message(messenger_id, text):
    # Package params into dictionaries for POST request
    recipient = {'id':messenger_id}
    message = {
        'text':text,
        'quick_replies':[
            {
                'content_type':'location'
            }
        ]
    }
    params = {
        'recipient':recipient,
        'messages':message
    }

    # Send POST request to Facebook Messenger Send API to send coordinates message
    r = requests.post(SEND_API_URL, json=params)
