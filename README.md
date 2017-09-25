# EM Slack Beer Alerts

Send new beer alerts to your [Slack](#disclaimer) channel based on tweets from your favorite breweries.

## Installation

1. Download this repository to your webserver:

    ```
    git clone https://github.com/ErinMorelli/em-slack-beer-alerts.git
    ```

2. Navigate into the folder created by step 1 and install the required python packages by running `pip`:

    ```
    pip install -r requirements.txt
    ```

3. Rename the `config/sample_twitter.yml` file to `config/twitter.yml` and add your own Twitter API credentials. Find instructions on how to get your credentials [here](https://python-twitter.readthedocs.io/en/latest/getting_started.html#getting-your-application-tokens).

4. Add the Twitter accounts and regular expressions that match the types of tweets you want to track to the `config/regexes.yml` file. Find more information on how to do this in the comments of that file.

5. Add the EM Slack Beer Alerts application to your Slack workspace using this link:

    https://hooks.erinmorelli.com/slack/beer-alerts/

6. Configure an [IFTTT](https://ifttt.com) applet to trigger this script based on tweets. For example, here is how I have configured mine:

    ### This:
    
    * **Trigger:** "Twitter" --> "New tweet from search"
    * **Search For:** "from:nightshiftbeer, OR from:trilliumbrewing, OR from:treehousebrewco exclude:replies exclude:retweets"

    ### That:
    
    * **Action:** "Webhooks" --> "Make a web request"
    * **URL:** "http://path/to/your/webserver/beer_alerts.py"
    * **Method:** "POST"
    * **Content Type:** "application/json"
    * **Body:**

        ```
        {
            tweet_url": {{LinkToTweet}},
            "user": {{UserName}},
            "webhook_urls": [
                "https://hooks.slack.com/services/your/slack/webhook_one",
                "https://hooks.slack.com/services/your/slack/webhook_two"
            ]
        }
        ```


## Disclaimers

[Slack.com](https://www.slack.com/) is not affiliated with the maker of this product and does not endorse this product.

Application icon made by [Freepik](http://www.freepik.com) from [www.flaticon.com](https://www.flaticon.com/) is licensed by [CC 3.0 BY](http://creativecommons.org/licenses/by/3.0)
