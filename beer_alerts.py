#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2017 Erin Morelli.

Title       : EM Slack Beer Alerts
Author      : Erin Morelli
Email       : erin@erinmorelli.com
License     : MIT
Version     : 0.1
"""

# Future
from __future__ import print_function

# Built-ins
import os
import re
import sys
import json
import logging

# Third-party
import yaml
import urllib3
import requests
from dateutil import parser, tz
from twitter import Twitter, OAuth

# Disable SSL warnings from the `requests` module
# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
urllib3.disable_warnings()


class EmSlackBeerAlert(object):
    """Class to create Slack beer alerts from tweets."""

    # Path to config files
    CONFIG = {
        'twitter': 'config/twitter.yml',
        'regexes': 'config/regexes.yml'
    }

    def __init__(self):
        """Initialize class and connect to Twitter."""
        self.args = {}
        self.tweet = None

        # Connect to twitter
        self._connect()

        # Get tweet and user
        self._get_args()

        # Get parser from user
        self._get_regexes()

    def _connect(self):
        """Connect to the Twitter API."""
        credentials_file = self.__class__.CONFIG['twitter']

        # Get Twitter API credentials
        # consumer_key, consumer_secret, token, token_secret
        credentials = yaml.load(open(credentials_file).read())

        # Connect to Twitter API
        self._twitter = Twitter(auth=OAuth(**credentials))

    def _get_args(self):
        """Parse JSON POST data and retrieve tweet data from Twitter API."""
        post_data = sys.stdin.read()

        # Parse JSON
        self.args = json.loads(post_data)
        logging.error(self.args)

        # Get tweet from ID
        self.tweet = self._twitter.statuses.show(
            id=self.args['tweet_url'].split('/').pop(),
            tweet_mode='extended'
        )

    def _get_regexes(self):
        """Locate RegExes from the config for the given Twitter user."""
        user = self.args['user'].lower()

        # Get path to regexes file
        regexes_file = self.__class__.CONFIG['regexes']

        # Get all regexes
        all_regexes = yaml.load(open(regexes_file).read())

        # Report error
        if user not in all_regexes.keys():
            sys.exit()

        # Set regexes for user
        self._regexes = all_regexes[user]

    def _validate_tweet(self):
        """Validate tweet content against RegExes.

        Returns:
            bool: True if the tweet is valid, otherwise False.

        """
        text = self.tweet['full_text']

        # Check for the positive regexes
        if 'positive' in self._regexes.keys():
            for raw_regex in self._regexes['positive']:
                regex = re.compile(raw_regex, re.I)
                if not regex.search(text):
                    return False

        # Check for the negative regexes
        if 'negative' in self._regexes.keys():
            for raw_regex in self._regexes['negative']:
                regex = re.compile(raw_regex, re.I)
                if regex.search(text):
                    return False

        # If we got this far, the tweet is valid
        return True

    def _parse_tweet(self):
        """Parse tweet content to extract images and display full URLs.

        Returns:
            str:  The parsed tweet text content.
            list: A list of photo URLs parsed from the tweet content.

        """
        text = self.tweet['full_text']

        # Get tweet entities
        urls = self.tweet['entities']['urls']
        media = self.tweet['entities']['media']
        photos = []

        # Get all images from tweet
        if media:
            for item in media:
                text = text.replace(item['url'], '')
                photos.append(item['media_url_https'])

        # Replace twitter URLs with the real expanded URLs
        if urls:
            for url in urls:
                text = text.replace(url['url'], url['expanded_url'])

        # Return with parsed text and list of photos
        return text, photos

    def _get_epoch_time(self):
        """Get tweet `created_at` time in Epoch format for the local TZ.

        Returns:
            int: Tweet `created_at` time in Epoch format.

        """
        created_at = parser.parse(self.tweet['created_at'])

        # Set up timezone objects
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        # Convert from UTC to local
        created_at = created_at.replace(tzinfo=from_zone)
        created_at_local = created_at.astimezone(to_zone)

        # Return in epoch format
        return int(created_at_local.strftime("%s"))

    def _get_alert_content(self):
        """Create a dict of Slack-friendly data to send via webhook.

        Return:
            dict: Formatted Slack webhook data. See more:
                  https://api.slack.com/incoming-webhooks#sending_messages

        """
        user = self.tweet['user']

        # Parse the tweet for images and links
        text, photos = self._parse_tweet()

        # Set image URLs
        image_url = photos[0] if photos else None
        thumb_url = '{url}:thumb'.format(url=photos[0]) if photos else None

        # Set up links
        title_link = "https://twitter.com/{usr}".format(usr=self.args['user'])
        footer = "<{link}|View on Twitter>".format(link=self.args['tweet_url'])

        # Return formatted response
        return {
            "text": ":beer: NEW BEER RELEASE ALERT! :beer:",
            "attachments": [
                {
                    "author_name": user['name'],
                    "author_link": user['url'],
                    "title": "@{user}".format(user=user['screen_name']),
                    "title_link": title_link,
                    "author_icon": user['profile_image_url_https'],
                    "text": text,
                    "image_url": image_url,
                    "thumb_url": thumb_url,
                    "footer": footer,
                    "footer_icon": "https://twitter.com/favicon.ico",
                    "ts": self._get_epoch_time()
                }
            ]
        }

    def execute(self):
        """Run tweet validation and send alert, if needed.

        Return:
            dict: HTTP response data from validation result.

        """
        is_valid = self._validate_tweet()

        # If the tweet is valid, send the alert
        if is_valid:
            response = self.send_alert()
        else:
            # Otherwise send unsent successful response
            response = {
                "status_code": 200,
                "reason": "OK"
            }

        # Return JSON response
        logging.error(response)
        return response

    def send_alert(self):
        """Send tweet alert to Slack via webhook URL.

        Returns:
            dict: HTTP response data from webhook request.

        """
        responses = []

        # Get alert content
        slack_data = self._get_alert_content()

        # Iterate over webhook URLs
        for webhook_url in self.args['webhook_urls']:

            # Make POST request to Slack webhook
            response = requests.post(
                webhook_url,
                data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )

            # Return JSON response
            responses.append({
                "status_code": response.status_code,
                "reason": response.reason
            })

        # Return responses
        return responses


# Run the script from the command-line
if __name__ == '__main__':
    # Check for POST request
    if os.environ['REQUEST_METHOD'] != 'POST':
        # Set response headers
        print("Status:405\r\nContent-type:application/json\r\n")

        # Send JSON body response
        print(json.dumps([{
            "status_code": 405,
            "reason": "Method Not Allowed"
        }]))

        # Exit program
        sys.exit()

    # Create a beer alert
    __response__ = EmSlackBeerAlert().execute()

    # Set response headers
    print("{status}\r\nContent-type:application/json\r\n".format(
        status="Status: {code}".format(code=200)
    ))

    # Send JSON body response
    print(json.dumps(__response__))
