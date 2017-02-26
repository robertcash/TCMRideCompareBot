# Script to send messages to FB Messenger via FB Messenger Send API
import requests

# Constants
FB_ACCESS_TOKEN = 'EAACXghObtBQBAMDKNthIe397xo507clgLHSrjQhU7FNsr6pAHKdjsG02ZCCDOdFDLZBHM3wquj2M3yQyhtywMpjuvqRG1iFxjToNe4eYoap1Q1ODt5sFBQB1ewccZAUU8AcKgj8PoatY4UeGZBmlaShxZCXZAVnvpZB6iD7306YbQZDZD'
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
