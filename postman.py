import json
import time
from flask import Flask, request, make_response
import requests
import os
from collections import deque
#import logging


import ssl
import urllib
 
ssl._create_default_https_context = ssl._create_unverified_context


app = Flask(__name__)


# Read the Microsoft Teams Incoming webhook URL from the environment
teams_webhook_url = os.environ.get('TEAMS_WEBHOOK_URL')

# Read the Slack bot token from the environment
slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')

# Read the Slack signing secret from the environment
slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET')


# Read the DingTalk incoming webhook URL from the environment
dingtalk_webhook_url = os.environ.get('DINGTALK_WEBHOOK_URL')

# List of organizations with their domain names
organizations = ["@abc.com"]

# Utility function to verify Slack requests
def verify_slack_request(request):
    from slack_sdk.signature import SignatureVerifier
    verifier = SignatureVerifier(signing_secret=slack_signing_secret)
    return verifier.is_valid_request(request.data, request.headers)

# Utility function to get user info from Slack API
def get_user_info(user_id):
    from slack_sdk import WebClient
    client = WebClient(token=slack_bot_token)

    try:
        response = client.users_info(user=user_id,include_email=True)
        user_info = response['user']
        return user_info
    except Exception as e:
        print(f"Error getting user info for user {user_id}: {e}")
        return None

# Utility function to check if a user is in any of the specified organizations
def is_user_in_organization(user_info):
    user_email = user_info.get('profile', {}).get('email', '')
    for org in organizations:
        if user_email.endswith(org):
            return True
    return False

def send_dingtalk_message(message):
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    response = requests.post(dingtalk_webhook_url, headers=headers, json=data)
    return response.json()


event_ids = deque(maxlen=100)

@app.route('/slack-to-teams', methods=['POST'])
def slack_to_teams():
    # Verify if the request is from Slack
    # print(request.json)
    if not verify_slack_request(request):
        return make_response("Request not verified", 403)
    

    # Process the event data
    event_data = request.json
    event_type = event_data.get('type')
    global event_ids
    event_id = event_data['event_id']

    if event_id is not None and event_id not in event_ids:
        # Handle URL verification during Event API setup
        if event_type == 'url_verification':
            return event_data["challenge"]

        # Forward message from users in specified organizations to Teams and DingTalk
        if event_type == 'event_callback':
            event = event_data['event']
            if event['type'] == 'message':
                if 'subtype' in event and event['subtype'] == 'message_changed':
                    event = event['message']
                user_id = event['user']
                user_info = get_user_info(user_id)
                # Only forward messages from users in specified organizations
                if user_info and is_user_in_organization(user_info):
                    # Log the event
                    message = event.get('text', '')
                    timestamp = event.get('ts')
                    username = user_info.get('name', 'unknown_user')

                    #TODO using gunicorn logger, e.g. app.logger.info(f'Message "{message}" from {username}')
                    print(f'[INFO] Message "{message}" from {username} at {time.ctime(float(timestamp))}')

                    # Create Microsoft Teams message
                    teams_payload = {
                        "@context": "https://schema.org/extensions",
                        "@type": "MessageCard",
                        "text": f"From {user_info['name']}: {message}",
                    }

                    # Send data to Microsoft Teams Incoming webhook
                    requests.post(teams_webhook_url, json.dumps(teams_payload), headers={'Content-Type': 'application/json'})

                    # Create DingTalk message
                    dingtalk_payload = f"From {user_info['name']}: {message}"
                    send_dingtalk_message(dingtalk_payload)

                    event_ids.append(event_id)

    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # gunicorn_logger = logging.getLogger('gunicorn.error')
    # app.logger.handlers = gunicorn_logger.handlers
    # app.logger.setLevel(gunicorn_logger.level)
    #app.run()

