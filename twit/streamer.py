import tweepy
import random
import logging
import winsound
from threading import Thread
from config import messages


class TwitStreamer(tweepy.StreamListener):
    """inherits from StreamListener"""
    

    def __init__(self, blacklist, interact, logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.blacklist = blacklist
        self.interact = interact
        super().__init__()
        
    
    def on_status(self, status):
        """on_status method, called when a new status arrives"""
        # drop retweets
        if hasattr (status, 'retweeted_status'):
            self.logger.info("Retweet by @%s dropped: %s",status.user.screen_name, status.text)
            return
        # drop known ac's
        username = status.user.screen_name
        if username in self.blacklist:
            self.logger.info('Blacklisted user dropped: @%s', username)
            return
        # Print Tweet and ask for user input
        print ('@{} tweeted: {}'. format(username, status.text))
        winsound.Beep(600, 1500) # Ring system bell
        # create an object and run it on a seperate thread
        user_choice = input("Do you want me to retweet them::>")
        # retweet or continue
        if user_choice.lower() == 'y':
            self.interact.retweet(username, status.id)
            self.logger.info('@%s retweed', username)
        else:
            self.logger.info('Tweet %s rejected for retweeting @%s',status.id, username)
            return


    def on_error(self, status_code):
        #print(status)
        if status_code == 420:
            self.logger.info("Disconnecting stream due to rate limit error")
            #returning False in on_data disconnects the stream
            return False


