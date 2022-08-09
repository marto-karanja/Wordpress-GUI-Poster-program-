# String cleaner class
import re
import logging
from engine.stop_words import BannedStrings

class Cleaner(object):
    """contains methods to clean strings"""
    def __init__(self, logger = None):
        """get logger object"""
        self.logger = logger or logging.getLogger(__name__)

    def clean_string(self, dirty_string):
        """Removes image tags and stop words"""
        # remove image tags
        dirty_string = re.sub("(<img.*?>)", "", dirty_string, 0, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        # remove stop words
        banned_strings = BannedStrings()

        stop_words = dict.fromkeys(banned_strings.stop_words, "")
        print(stop_words)

        # use these three lines to do the replacement
        rep = dict((re.escape(k), v) for k, v in stop_words.items())
        #re.I if ignore_case else 0 # turn off case due to bug
        pattern = re.compile("|".join(rep.keys()))
        clean_string = pattern.sub(lambda m: rep[re.escape(m.group(0))], dirty_string)
        if dirty_string != clean_string:
            self.logger.warning("Stop words removed")
        return clean_string
    
    def clean_content(self, dirty_string):
        """Performs additional content formatting"""
        content_length = len(dirty_string.split())
        self.logger.debug("String length: %s", content_length)
        if (content_length > 80):
            dirty_string = self.clean_string(dirty_string)
            return dirty_string
        else:
            # log short content instance
            self.logger.error("The string was too short")
            return False
    
    def clean_title(self, dirty_string):
        """Performs additional string formatting"""
        dirty_string = self.clean_string(dirty_string)
        # welcome_string = '[Solved]'
        clean_string = dirty_string
        return clean_string

    def add_meta_content(self, content, category):
        """Adds additional meta content to the content string"""
        clean_string = ""
        """Add marketing jargon"""
        #meta_content="<table style = 'table-striped table-bordered table-hover' responsive='true'><tr><th>Question</th></tr><tr><td>{question}</td></tr></table>"
        #clean_string = meta_content.format(question = content)
        clean_string = content
        return clean_string