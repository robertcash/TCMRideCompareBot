# RideCompareBot


RideCompareBot is a tutorial Messenger bot created for the Think Code Make class at Goizueta Business School at Emory University. It is written in Python 3 using the Flask web framework.

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
received_message = MessengerParser(request)
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
        if message.get('attachments'):
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

After we get our text, we then need to send that text to Google's translation API. We do this with the following line of code:

```
# Uses translate_message function in google_api_requests.py to translate user message
    translation = translate_message(received_message.text, TARGET_LANGUAGE)
```

In that line, we are calling the translate_message function we imported from google_api_requests.py. We are passing the text property of the received_message variable along with a defined constant at the top of the file that contains a language code for the target language we want to translate to.

In that function, we send a GET request to Google's Translation API with a packet of our own JSON that contains the needed data to get the translation. After we send the request, we check if it was a successful request (If the status code is 200, that means it was successful), and if it is, we grab data from the JSON Google sent us just like we did with Facebook to get our translated text.

```
def translate_message(text, target_lang):
    # Package params into dictionary for GET request.
    params = {
        'key':GOOGLE_API_KEY,
        'q': text,
        'source': 'en',
        'target': target_lang
    }

    # Send POST request to Google.
    r = requests.get(GOOGLE_TRANSLATE_URL, params=params)

    # Check if success, if success, return translated text. If not, return error message.
    if r.status_code != 200:
        return 'Something wrong happened, try again later!'

    translated_text = r.json()['data']['translations'][0]['translatedText']
    return translated_text
```

This is how the translated text JSON that Google sends us looks like:

```
{
  "data": {
    "translations": [
      {
        "translatedText": "Olá Mundo!"
      }
    ]
  }
}
```

Now the only task left is for our bot to actually send the translated text to the user so they can see it in their Messenger thread. This is done with this line in bot.py:

```
# Uses send_message function in messenger_parser.py to send translated message back to user
    send_message(received_message.messenger_id, translation)
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

#### 3. Getting the Uber API Key

#### 4. Getting a Facebook Page Access Token
We need an access token to send messages to the bot connected with our Page, but first we need a page. Go to your regular Facebook and create a page, this is all you have to do for this step, it's pretty simple.

Next, go to https://developers.facebook.com/ and become a developer. After you do this, follow the steps on this page: https://developers.facebook.com/docs/messenger-platform/guides/quick-start, but ignore step 2 "Setup Webhook" (this comes after we deploy to Heroku) and don't bother with the code or steps 5-8.

Now you should have an access token, go copy and paste this at this line of code in messenger_api_requests.py:

```
FB_ACCESS_TOKEN = 'YOUR ACCESS TOKEN HERE'
```

#### 5. Getting a Amazon RDS Setup

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
