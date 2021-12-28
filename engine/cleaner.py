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
        return clean_string
    
    def clean_content(self, dirty_string):
        """Performs additional content formatting"""
        if len(dirty_string) > 600:
            dirty_string = self.clean_string(dirty_string)
            return dirty_string
        else:
            # log short content instance
            self.logger.debug("The string was too short: %s", dirty_string)
            return False
    
    def clean_title(self, dirty_string):
        """Performs additional string formatting"""
        dirty_string = self.clean_string(dirty_string)
        #welcome_string = 'Order the answer to: '
        #clean_string = welcome_string + dirty_string
        return dirty_string

    def add_meta_content(self, content, category):
        """Adds additional meta content to the content string"""
        clean_string = ""
        """Add marketing jargon"""
        meta_content="<table style = 'table-striped table-bordered table-hover' responsive='true'><tr><th>Question</th><td>{question}</td></tr><tr><th>Subject</th><td>{category}</td></tr></table>"
        clean_string = meta_content.format(question = content, category = str(category[0]))
        return clean_string