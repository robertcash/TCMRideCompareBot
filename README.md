# TCMRideCompareBot


TCMRideCompareBot is a tutorial Messenger bot created for the Think Code Make class at Goizueta Business School at Emory University. It is written in Python 3 using the Flask web framework.

Messenger Bots are chatbots that can answer messages to your Facebook page. They're like mini-apps you can message in Messenger that can serve users without having to be downloaded. Technical-wise, they are server-side applications with one webhook. Facebook sends requests to this webhook every time a user messages your bot. Your application does it's job (i.e.: sending a translated message to the user) and then it completes Facebook's request with a response.

### So What Does This Tutorial Cover?

  - A Messenger bot that finds out if Lyft or Uber is cheaper given a start and end destination.
  - Google Places API, Lyft API, and Uber API.
  - Deployment of server-side applications to Heroku.

### Installation Setup

If you're already in TCM, you already have Python 3 installed on your machine. If you don't have Python 3 installed on your machine, follow these links:
  - MacOS/Linux: http://docs.python-guide.org/en/latest/starting/installation/
  - Windows: http://www.openbookproject.net/courses/webappdev/units/softwaredesign/resources/install_python_win7.html

In order to run your ride compare bot, you must deploy it to Heroku or run the Python program locally using ngrok (https://ngrok.com) to create a secure endpoint for Facebook. In this tutorial, I will go over deploying your bot to Heroku, but if you want to go the ngrok route, their website will tell you how to install and setup.

In order to deploy to Heroku from your machine, we must install git and the Heroku command line interface (CLI). To install git, follow this link: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git. To install the Heroku command line interface, follow this link: https://devcenter.heroku.com/articles/heroku-cli. Don't forget to make an account on Heroku as well, it's free.

You will also need to make an account on Amazon Web Services (https://aws.amazon.com/). Don't worry it is free.

Now we have all the tools we need to run the bot.

### Project Organization

This bot has multiple files and is structured as followed:

- application.py - this file is what is ran by the local machine and/or machine on Heroku to run your application. It contains the endpoint for the webhook that is called by Facebook. This is like the entry point that houses the path to the brain of the application, bot.py.
- bot.py - this file is the brain of the application. It houses the central logic of the bot and it uses functions in other files for specific tasks in order for the bot to do its job. Once the job is done, it sends a success response to Facebook.
- messenger_parser.py - this file contains a class that takes in the request Facebook sends to your application and gets the text or coordinates the user sent along with the id of the user who sent it so you can later send a message back to that user.
- google_api_requests.py - this file contains a function that sends a request to Google Places API to translate a location name or address to coordinates.
- messenger_api_requests.py - this file contains a function that sends text back to the user who sent the message in the first place.
- compare_api.py - this file contains a function to that sends all location data to Lyft and Uber API's to their cost estimate endpoints and does a comparison in price between both rideshare companies.
- helpers.py - this file contains a helper function that creates a success response. This is used by bot.py when the bots task is done so Facebook's request to our bot is completed.
- Procfile and requirements.txt - these files are just used by Heroku to run your app so you can ignore them. requirements.txt just tells Heroku what dependencies your application needs and the Procfile tells Heroku what file to run.

### Bot Creation Steps

In this section, I will cover the important parts of the code of this project. You can skip this step if you don't care about the implementation details because you can just run this project code on Heroku to get a working bot.

#### 1. Creating the Flask App

We need to use Flask, a web framework, to have a server-side application that lives in the cloud. The code for this is rather vanilla and is a simple copy and paste for the most part from the application.py file to create the Flask app, but I will focus on the unique part here. If you're intetested in the nuts and bolts of that vanilla code, Flask has great documentation on their site here: http://flask.pocoo.org.

```
@application.route('/webhook', methods=['GET', 'POST'])
def webhook():
    try:
        if request.method == 'GET':
            # Webhook is verified with Facebook Messenger https://developers.facebook.com/docs/graph-api/webhooks
            if request.args.get('hub.verify_token') == '12345':
                return Response(request.args.get('hub.challenge'))
            else:
                return Response('Wrong validation token.')
        else:
            # Here messages in a form of JSON are received, code for this is handled in bot.py
            return bot.response_handler(request.get_json())
    except:
        return Response('Application error.')
```

The above code is a route. A route in layman's terms is a path in your application that is called upon to perform a specific bunch of code. So if you enter https://ridecomparebot.herokuapp.com/webhook into your web browser, you should see a webpage with "Wrong validation token." because the web browser performed a GET request and I didn't provide a validation token. If you haven't noticed, the slash in the url is the same as the slash in this line of code:

```
@application.route('/webhook', methods=['GET', 'POST'])
```
This is because that's exactly how websites are setup behind the scenes, with routes.

What Facebook does is send a POST request to this route via that url above and so in the code the line:
```
return bot.response_handler(request.get_json())
```
is called.

#### 2. Creating the Bot Logic
Once Facebook calls that route, this function is triggered:

```
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
```

We are given the message data from the user in the form of JSON. JSON in layman's terms is a packet of organized data we use to send to places like servers and devices. It is key-value in nature which means if you want the value of the key "text", all you have to do is access the key "text" and you should get that text.

In bot.py, this line of code:

```
messenger_parser = MessengerParser(request)
```

creates an object called MessengerParser that does this when we pass it the JSON, in the form of a Python dictionary, in the variable "request".

Inside the initializer of the class MessengerParser, it takes in the JSON and grabs the needed data to grab the user's message and the user's messenger id so we can send the user a message back. We put those two variables into the properties "self.text" and "self.messenger_id" so later we can use the variable "received_message" from above to grab those entities. If the user sends location data, we can grab the user's coordinates from the JSON as well.

```
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
        if 'attachments' in message:
            attachments = message['attachments']
            coordinates = attachments[0]['payload']['coordinates']
            self.lat = coordinates['lat']
            self.lng = coordinates['long']
        else:
            # Normal text message
            self.text = message['text']
```

For reference, here is how the JSON really looks like:

```
# For a text message
{
  "object":"page",
  "entry":[
    {
      "id":"PAGE_ID",
      "time":1458692752478,
      "messaging":[
        {
          "sender":{
            "id":"USER_ID"
          },
          "recipient":{
            "id":"PAGE_ID"
          },
         "timestamp":1458692752478,
         "message":{
         "mid":"mid.1457764197618:41d102a3e1ae206a38",
         "seq":73,
         "text":"hello, world!"
        }
      ]
    }
  ]
}

# For a coordinates message
{
  "object": "page",
  "entry": [
    {
      "id": "PAGE_ID",
      "time": 1472672934319,
      "messaging": [
        {
          "sender": {
            "id": "USER_ID"
          },
          "recipient": {
            "id": "PAGE_ID"
          },
          "timestamp": 1472672934259,
          "message": {
            "mid": "mid.1472672934017:db566db5104b5b5c08",
            "seq": 297,
            "attachments": [
              {
                "title": "Facebook HQ",
                "url": "https://www.facebook.com/l.php?u=https%....5-7Ocxrmg",
                "type": "location",
                "payload": {
                  "coordinates": {
                    "lat": 37.483872693672,
                    "long": -122.14900441942
                  }
                }
              }
            ]
          }
        }
      ]
    }
  ]
}    
```

After we get our data and our messenger_id, we then need to grab the user associated by it from our database so we can get the last action the user did. The user could be brand new so we must make a new user in the database corresponding to the given messenger_id if that's the case:

```
try:
      user = User.select().where(User.messenger_id == messenger_parser.messenger_id).get()
  except:
      # If user doesn't exist, we create them. This would be a first time user.
      user = User.create(messenger_id=messenger_parser.messenger_id, state='ask_start')
```

Once we either make a new user or grab our existing user, we need to check what state they were in when they last messaged the bot. There's three possible states in our bot, "ask_start" (a state where the user is asked their current location), "ask_end" (a state where the user provides where they want to go), and "give_result" (a state where the result is given). Each state has its own function that is called in bot.py to handle them.

```
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
```

If the user is in the "ask_start" state, we must send them a special message that allows them to send their location. This is done here:

```
def start_handler(user):
    # Send coordinates message to receive the user's current location
    send_coordinates_message(user.messenger_id, 'What\'s your current location?')

    # Change the user state to ask_end so the next time the user sends a message, it asks for where they want to go.
    user.state = 'ask_end'
    user.save()
```

and specifically this function in messenger_api_requests.py:

```
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
        'message':message
    }

    # Send POST request to Facebook Messenger Send API to send coordinates message
    r = requests.post(SEND_API_URL, json=params)
```

As you can you see after sending our message, we convert the user to the next state "ask_end" so when the user next messages the bot, they will be in the step where they provide where they want to go.

In the next state, we receive the coordinates from our message_parser and we save it to our user object in our database so we can refer to it later when we do the comparisons because variables with network requests aren't saved from request to request in a regular running program. We do this with these lines:

```
  user.start_lat = messenger_parser.lat
  user.start_lng = messenger_parser.lng
```

Our user object saves the following things as seen in db.py:

```
# This is our User object with all the attributes it saves
class User(BaseModel):
    user_id = PrimaryKeyField(db_column='user_id')
    messenger_id = CharField(db_column='messenger_id', null=True)
    state = CharField(db_column='state', null=True)
    start_lat = FloatField(db_column='start_lat', null=True)
    start_lng = FloatField(db_column='start_lng', null=True)

    class Meta:
        db_table = 'User'
```

Here's the rest of the code for end handler:

```
def end_handler(messenger_parser, user):
    # Get user location coordinates from message
    user.start_lat = messenger_parser.lat
    user.start_lng = messenger_parser.lng

    # Send message asking where the user wants to go
    send_message(user.messenger_id, 'Where do you want to go?')

    # Change the user state to give_result so the next time the user sends a message, it gives what rideshare is cheaper.
    user.state = 'give_result'
    user.save()
```

We change our state to "give_result" so when the user does put where they want to go, it will then trigger the comparison between Lyft and Uber.

In result_handler, we need to convert the user text to coordinates, this is done with the Google Places API. We also need to do our comparisons, which is done with the Lyft and Uber APIs.

```
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
        message_to_send = result['winner'].capitalize() + ' is cheaper! It costs $' + str(result['cost']) + '!'
        send_message(user.messenger_id, message_to_send)

    # Change the user state to ask_start so the next time the user sends a message, it starts the process over again.
    user.state = 'ask_start'
    user.save()
```

To get our coordinates, we are call the get_coordinates function we imported from google_api_requests.py. We are passing the text property of the messenger_parser variable to get our coordinates.

In that function, we send a GET request to Google's Places API with a packet of our own data that contains the needed data to get the translation. After we send the request, we check if it was a successful request (If the status code is 200, that means it was successful), and if it is, we grab data from the JSON Google sent us just like we did with Facebook to get our translated text.

```
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
```

Now the only task left is for our bot to actually do the comparison of what is cheaper by giving our start and end coordinates to both the Lyft and Uber API's cost estimators. This is done with the compare function imported from the compare_api.py file:

```
def compare(start_lat, start_lng, end_lat, end_lng):
    # Create params for API requests to Lyft and Uber
    lyft_params = {
        'start_lat':start_lat,
        'start_lng':start_lng,
        'end_lat':end_lat,
        'end_lng':end_lng
    }
    lyft_headers = {
        'Authorization':'bearer ' + LYFT_KEY
    }
    uber_params = {
        'start_latitude':start_lat,
        'start_longitude':start_lng,
        'end_latitude':end_lat,
        'end_longitude':end_lng
    }
    uber_headers = {
        'Authorization':'Token ' + UBER_KEY
    }

    # Do API Requests to Lyft and Uber
    lyft_request = requests.get(LYFT_URL, params=lyft_params, headers=lyft_headers)
    uber_request = requests.get(UBER_URL, params=uber_params, headers=uber_headers)

    # Check if both requests were succesful
    if lyft_request.status_code != 200 or uber_request.status_code != 200:
        return {'success':False}

    # Get estimates from both requests
    lyft_cost_estimates = lyft_request.json()['cost_estimates']
    uber_cost_estimates = uber_request.json()['prices']

    # Check to see what is cheaper and send it back to the user
    lyft_cost = sys.maxint
    uber_cost = sys.maxint

    for estimate in lyft_cost_estimates:
        lyft_cost = min(lyft_cost, (estimate['estimated_cost_cents_min']/100))
        if estimate['ride_type'] == 'lyft':
            break

    for estimate in uber_cost_estimates:
        uber_cost = min(uber_cost, estimate['low_estimate'])
        if estimate['display_name'] == 'uberX':
            break

    if lyft_cost > uber_cost:
        # Uber is cheaper
        return {'success':True, 'winner':'uber', 'cost':uber_cost}

    return {'success':True, 'winner':'lyft', 'cost':lyft_cost}
```

We create our packets of data to send to Lyft and Uber in lyft_params and uber_params variables. We then make our request and go through the results. We must loop through all the results we received as both Lyft and Uber offer different kind of cars. We are specifically comparing regular Lyfts and Ubers so we run through all the estimates until we get the ride type of "lyft" and the display_name of "uberX" for Uber. Once we have both of those, we compare the cost in total dollar amount. The winner is then sent back to our results_handler function with the winner name and cost in a dictionary.

Lastly, we send the result to our user.

```
  message_to_send = result['winner'].capitalize() + ' is cheaper! It costs $' + str(result['cost']) + '!'
  send_message(user.messenger_id, message_to_send)
```

The line above calls the send_message function we imported from messenger_api_requests.py with the messenger_id property from received_message and the translation. The function itself does something similar to the translate_message function, but instead of sending a GET request to Google, it sends a POST request to Facebook's Messenger Bot API.

```
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
```

The last few lines of our results_handler resets the user state to the beginning so they can give us another starting location for the next time they use our bot.

```
  # Change the user state to ask_start so the next time the user sends a message, it starts the process over again.
  user.state = 'ask_start'
  user.save()
```

You may be wondering what's the difference between GET and POST at this point. They're both HTTP request methods, but GET requests data from a server while POST submits data to a server. As you may have noticed, we sent data to a URL each time we used this, and that is because you can use both of these methods to do both of the jobs I've mentioned. It's just good practice to use GET when requesting data and POST for when you're sending data to be stored or processed for the sake of standardization. One advantage POST has is that the data sent through POST can be encrypted while with GET it's open for the world to see.

So at this point, we've finished all the tasks our bot needs to do to translate a user's message into a different language and send the translation back. Now all we have to do is send a success response back to Facebook just like how Google sent us one after they translated our message. If we don't send back this message back, Facebook will think something went wrong and will turn off our bot. We do this with the following line:

```
# Ends FB's webhook request with a response with a 200 success code
    return response()
```

The response functon is imported from helpers.py and it just sends empty JSON back with a 200 success code.

```
def response():
    # Sends 200 success response
    response = jsonify({})
    response.status_code = 200
    return response
```

We are now done with our bot, all we have to do is get it online!

### Getting the Bot Online

This is the most annoying part of the process of creating a bot. Google's API site is notoriously confusing, Heroku can be a bit scary the first time, and Facebook's docs on linking a bot to a page can be a little tricky. With this step, we will also be filling in the empty GOOGLE_API_KEY and FB_ACCESS_TOKEN variables we saw in our files.  

#### 1. Getting the Google API Key

First thing to conquer is getting an API key so we can call Google's Translation API. An API key is needed because Google's API's are services that aren't free so this is how they monitor who uses their API's.

After you make a Google Cloud Platform account at https://cloud.google.com, go to "library" in the API manager in your console (https://console.cloud.google.com/apis/library), from here find "Translation API" under "Google Cloud Machine Learning". Once you've clicking on "Translation API", select the option to enable the API.

The last step after enabling the API is getting an API key. Go to "credientials" under the API manager (https://console.cloud.google.com/apis/credentials) and click "Create Credentials" and select "API Key". Now you should have an API key, go copy and paste this at this line of code in google_api_requests.py:

```
GOOGLE_API_KEY = 'YOUR API KEY HERE'
```

#### 2. Getting the Lyft API Key

Go to https://www.lyft.com/developers and click on manage apps in the top right corner of the page. Select "Create App" after logging in then enter all the necessary details. You then should taken to your app page, click on "show credentials" and copy and paste the client token to compare_api.py to the LYFT_KEY variable.

#### 3. Getting the Uber API Key

Go to https://developer.uber.com. Press sign in the top right and select "New App" once you login. Leave the selection on Ride API and fill in the necessary details. After that you should be on your app page. Copy and paste the "server token" to compare_api.py to the UBER_KEY variable.

#### 4. Getting a Facebook Page Access Token
We need an access token to send messages to the bot connected with our Page, but first we need a page. Go to your regular Facebook and create a page, this is all you have to do for this step, it's pretty simple.

Next, go to https://developers.facebook.com/ and become a developer. After you do this, follow the steps on this page: https://developers.facebook.com/docs/messenger-platform/guides/quick-start, but ignore step 2 "Setup Webhook" (this comes after we deploy to Heroku) and don't bother with the code or steps 5-8.

Now you should have an access token, go copy and paste this at this line of code in messenger_api_requests.py:

```
FB_ACCESS_TOKEN = 'YOUR ACCESS TOKEN HERE'
```

#### 5. Getting a Amazon RDS Setup along with your MySQL Database

This part is the most annoying part of all the steps. If you've haven't already made an AWS account as directed to at the beginning of the tutorial, please do so now.

THIS PART IS UNDER CONSTRUCTION

#### 6. Deploying to Heroku

If you've made a Heroku account (heroku.com) and installed git and the Heroku CLI (details in the installation part of the tutorial), you're ready for this step.

First we need to init our git repository in order to push our application to Heroku. We need to enter git commands in Terminal (if on MacOS/Linux) or Command Prompt (if on Windows) in the directory where your files are for your application. If you need help learning terminal/command prompt commands to get to your directory, go here:
- For MacOS/Linux: http://www.dummies.com/computers/macs/mac-operating-systems/how-to-use-basic-unix-commands-to-work-in-terminal-on-your-mac/
- For Windows: http://www.digitalcitizen.life/command-prompt-how-use-basic-commands

Here are the commands you need to enter:

```
git init
git add .
git commit -m "First Commit"
```

We are all set with git and now it's time to create our Heroku application so we can deploy our bot. First we need to login to Heroku from the command line with this command:

```
heroku login
```

Next we need to enter this command:

```
heroku create YOUR-APP-NAME-HERE
```

We have now created your Heroku application and now the only left to do is deploy! Enter this command and your bot should be live on Heroku.

```
git push heroku master
```

To find the URL of your application on Heroku, go to your Heroku dashboard (https://dashboard.heroku.com/apps) and find your app under "Personal apps". Next click "settings" and find "Domain" under "Domains and certificates". That URL is your application URL you give to Facebook with the "/webhook" route like this: "https://eng2port.herokuapp.com/webhook".

#### 7. Subcribing the Webhook to Facebook

Now that you've deployed your application and have a URL for it, we can follow step 2 at this link: https://developers.facebook.com/docs/messenger-platform/guides/quick-start. Make sure you give Facebook your /webhook route in the url like this: https://eng2port.herokuapp.com/webhook. After you do this, go ahead and message your bot from the page you created!

### You Did It!

Congratulations you built your first Messenger bot! Take this code and build your own Messenger bots!
