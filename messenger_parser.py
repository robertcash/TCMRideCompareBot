# Class to parse JSON request from FB server

class MessengerParser:
    # Initializer for class, what needs to be called when creating MessengerParser object
    def __init__(self, request):
        # Grab first message in list of messages in JSON request
        message_body = request['entry'][0]['messaging'][0]

        # Grab sender messenger id to keep track of who sent the message
        self.messenger_id = message_body['sender']['id']

        # Grab message body out of JSON
        message = message_body['message']

        # Check if the message body has an attachment, this means we are receiving coordinates (https://developers.facebook.com/docs/messenger-platform/send-api-reference/quick-replies)
        self.lat = 0
        self.lng = 0
        if 'attachments' in message:
            attachments = message['attachments']
            coordinates = attachments[0]['payload']['coordinates']
            self.lat = coordinates['lat']
            self.lng = coordinates['long']
        else:
            # Normal text message
            self.text = message['text']
