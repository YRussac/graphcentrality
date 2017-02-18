# -*- coding: utf-8 -*-

import json
import os
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from datetime import datetime
import tweepy
import time

# Twitter API Authentication
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
OAUTH_TOKEN = os.environ["OAUTH_TOKEN"]
OAUTH_TOKEN_SECRET = os.environ["OAUTH_TOKEN_SECRET"]
auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
api = tweepy.API(auth)


def timeline_encoder(obj):
    """JSON serializer for datetime type (that are returned from created_at tweet request)"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def user_information(user_id, number_of_tweets=200):
    """
    Prints a JSON object containing informations about a given Twitter user (name, followers count, friends count...)
    :param user_id: string, Twitter user id
    :param number_of_tweets: int, number of tweets we want to fetch for the given user
    """
    user = api.get_user(user_id)

    d_json = {"screen_name": user.screen_name,  "followers_count": user.followers_count,
              "friends_count": user.friends_count, "user_location": user.location, "tweets": [], "id": user_id}

    statuses = api.user_timeline(user_id, count=number_of_tweets)

    for tweet in statuses:

        d_tweet = {"tweet_id": tweet.id_str, "text": tweet.text, "tweet_geo": tweet.geo,
                   "hashtags": [hashtag['text'] for hashtag in tweet.entities["hashtags"]],
                   "user_mentions": [user_mention['id_str'] for user_mention in tweet.entities["user_mentions"]],
                   "date": tweet.created_at}
        d_json["tweets"].append(d_tweet)

    print(json.dumps(d_json, default=timeline_encoder))
    print("ℵ")
    return True

# Class used to stream Twitter incoming tweets
class StdOutListener(StreamListener):

    def __init__(self, time_limit=86400):
        self.initial_time = time.time()
        self.time_limit = time_limit

    def on_data(self, data):

        decoded = json.loads(data)

        user_id = decoded["user"]["id_str"]

        if user_id not in observed_users.keys():
            # New user
            # We add the information for this unobserved user
            too_many_requests = True
            while too_many_requests:
                try:
                    user_information(user_id, 200)
                    observed_users[user_id] = 1
                    too_many_requests = False
                except:
                    time.sleep(10)
        else:
            observed_users[user_id] += 1

        if (time.time() - self.initial_time) > self.time_limit:
            # If we exceed time limit
            # Prints the dictionary in which the keys are the users id and the values the number of occurences of those
            # users while we streamed
            print(json.dumps(observed_users))
            # Exits the program
            exit()

        return True

    def on_error(self, status):
        pass

if __name__ == '__main__':

    observed_users = {}
    # The program will run for 24 hours
    l = StdOutListener(time_limit=86400)
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    stream = Stream(auth, l)

    # This line filters Twitter Stream to capture data of users who use hashtags related to the French candidates for
    # the presidential election

    while True:
        try:
            stream.filter(track=["#Macron2017", "#Hamon2017", "#MLP2017", "#Fillon2017", "#JLM2017", "#NDA2017",
                                 "#Jadot2017"])
        except AttributeError:
            time.sleep(10)
