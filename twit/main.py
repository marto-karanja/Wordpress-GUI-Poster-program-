import tweepy
import random
import logging
import os
from datetime import date
from config import kip_keys, messages, blacklist
from streamer import TwitStreamer



CONSUMER_KEY = kip_keys['consumer_key']
CONSUMER_SECRET = kip_keys['consumer_secret']
ACCESS_TOKEN = kip_keys['access_token']
ACCESS_TOKEN_SECRET = kip_keys['access_token_secret']

# create OAuthhandler instance
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Api instance
api = tweepy.API(auth) # API object

class Interact(object):
    """ class to hold methods to interact with user"""
    def __init__(self, logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.api = tweepy.API(auth)
    
    def retweet(self, username, status_id):
        """Called when retweet action is specified"""
        self.logger = logging.getLogger(__name__)
        # fetch random message
        msg = messages[random.randint(0, (len(messages)-1))]
        self.api.update_status(msg.format(username), in_reply_to_status_id=status_id)
        self.logger.debug("@%s has been retweeted", username)



      

def run_app():
    """initialize"""
    # create a stream object
    d = date.today()

    log_file = d.isoformat()
    log_path = os.getcwd()
    logging.basicConfig(
    format="%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s",
    datefmt="'%m/%d/%Y %I:%M:%S %p",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format(log_path, log_file)),
        logging.StreamHandler()
    ],
    level = logging.INFO)

    logger = logging.getLogger(__name__) # logging object
    interact = Interact()
    twita_listener = TwitStreamer(blacklist,interact, logger)
    logger.info("Creating streamer object")
    # get stream instance 
    twita = tweepy.Stream(auth, twita_listener)
    logger.info("Getting stream instance.")
    logger.info("Waiting for tweets:")
    twita.filter(track=['essay pay', 'assignment pay', 'dissertation pay'])
    
    
if __name__ == '__main__':
    run_app()
  