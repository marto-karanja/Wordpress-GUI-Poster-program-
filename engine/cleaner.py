# String cleaner class
import re
import logging

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
        stop_words = {"please": "", "help": "", "thank" : "", "Please": "", "Help": "", "Thank" : ""} # define desired replacements here

        # use these three lines to do the replacement
        rep = dict((re.escape(k), v) for k, v in stop_words.items())
        #re.I if ignore_case else 0 # turn off case due to bug
        pattern = re.compile("|".join(rep.keys()))
        clean_string = pattern.sub(lambda m: rep[re.escape(m.group(0))], dirty_string)
        if dirty_string != clean_string:
            self.logger.warning("Stop words removed")
        return dirty_string
    
    def clean_content(self, dirty_string):
        """Performs additional content formatting"""
        if len(dirty_string) > 80:
            dirty_string = self.clean_string(dirty_string)
            return dirty_string
        else:
            # log short content instance
            self.logger.debug("The string was too short: %s", dirty_string)
            return False
    
    def clean_title(self, dirty_string):
        """Performs additional string formatting"""
        dirty_string = self.clean_string(dirty_string)
        welcome_string = 'Order answer: '
        dirty_string = welcome_string + dirty_string
        return dirty_string