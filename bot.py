from messenger_parser import MessengerParser
from db import User
from helpers import response
from google_api_requests import get_coordinates
from messenger_api_requests import send_message, send_coordinates_message
from compare_api import compare

def response_handler(request):
    # Parse request and get the data we want out of it like messenger_id, text, and coordinates.
    messenger_parser = MessengerParser(request)

    # Get user object from database so we can see the state of our user.
    try:
        user = User.select().where(User.messenger_id == messenger_parser.messenger_id).get()
    except:
        # If user doesn't exist, we create them. This would be a first time user.
        user = User.create(messenger_id=messenger_parser.messenger_id, state='ask_start')

    # Here we need to decide what we need to do next for our user
    if user.state == 'ask_start':
        # We need to ask our user where they are.
        start_handler(user)
    elif user.state == 'ask_end':
        # We need to ask our user where they are going.
        end_handler(messenger_parser, user)
    else:
        # We got all our information from our user and now we check what rideshare is cheaper and give results.
        results_handler(messenger_parser, user)

    # We are all done so just return the typical response to Facebook.
    return response()

def start_handler(user):
    # Send coordinates message to receive the user's current location
    send_coordinates_message(user.messenger_id, 'What\'s your current location?')

    # Change the user state to ask_end so the next time the user sends a message, it asks for where they want to go.
    user.state = 'ask_end'
    user.save()

def end_handler(messenger_parser, user):
    # Get user location coordinates from message
    user.start_lat = messenger_parser.lat
    user.start_lng = messenger_parser.lng

    # Send message asking where the user wants to go
    send_message(user.messenger_id, 'Where do you want to go?')

    # Change the user state to give_result so the next time the user sends a message, it gives what rideshare is cheaper.
    user.state = 'give_result'
    user.save()

def results_handler(messenger_parser, user):
    # Use Google Places API to get the coordinates of the address/business the user gives.
    end_coordinates = get_coordinates(messenger_parser.text, user)

    # Check if coordinate retrieval was a success. If not send message asking location again.
    if end_coordinates[0] == 0 and end_coordinates[1] == 0:
        send_message(user.messenger_id, 'Where do you want to go?')
        return

    # Now that we have all the coordinates needed, run code to compare prices using both Lyft and Uber API's.
    result = compare(user.start_lat, user.start_lng, end_coordinates[0], end_coordinates[1])

    # Send results back in a message to the user if comparison is successful. If not, send error.
    if not result['success']:
        send_message(user.messenger_id, 'Something wrong happened, try again!')
    else:
        # With winner, dictate deep link for user to click to open the app with the ride on their phone
        winner = result['winner'].capitalize()
        if winner == 'Uber':
            deep_link = 'uber://?action=setPickup&pickup[latitude]=' + str(user.start_lat) + '&pickup[longitude]=' + str(user.start_lng) + '&dropoff[latitude]=' + str(end_coordinates[0]) + '&dropoff[longitude]=' + str(end_coordinates[1])
        else:
            deep_link = 'lyft://ridetype?id=lyft&pickup[latitude]=' + str(user.start_lat) + '&pickup[longitude]=' + str(user.start_lng) + '&destination[latitude]=' + str(end_coordinates[0]) + '&destination[longitude]=' + str(end_coordinates[1])

        message_to_send = winner + ' is cheaper! It costs $' + str(result['cost']) + '! Tap here to call your ride: ' + deep_link
        send_message(user.messenger_id, message_to_send)

    # Change the user state to ask_start so the next time the user sends a message, it starts the process over again.
    user.state = 'ask_start'
    user.save()
