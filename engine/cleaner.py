# String cleaner class
import re
import logging
import random
from engine.stop_words import BannedStrings
from engine.local_db import fetch_references, connect_to_db

class Cleaner(object):
    """contains methods to clean strings"""
    def __init__(self, logger = None):
        """get logger object"""
        self.logger = logger or logging.getLogger(__name__)
        self.banned_strings = BannedStrings()
        self.engine = connect_to_db()

    def clean_string(self, dirty_string):
        """Removes image tags and stop words"""
        # remove image tags
        dirty_string = re.sub("(<img.*?>)", "", dirty_string, 0, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        # remove stop words
        

        stop_words = dict.fromkeys(self.banned_strings.stop_words, "")
        print(stop_words)

        # use these three lines to do the replacement
        rep = dict((re.escape(k), v) for k, v in stop_words.items())
        #re.I if ignore_case else 0 # turn off case due to bug
        pattern = re.compile("|".join(rep.keys()))
        clean_string = pattern.sub(lambda m: rep[re.escape(m.group(0))], dirty_string)
        if dirty_string != clean_string:
            self.logger.warning("Stop words removed")
        return clean_string
    
    def clean_content(self, dirty_string, content_length):
        """Performs additional content formatting"""
        content_length = len(dirty_string.split())
        self.logger.debug("String length: %s", content_length)
        if (content_length >= content_length):
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

        #clean_string = filter(lambda x: x.isalpha(), dirty_string)
        #clean_string.strip(":,<>!@$^&*()_-+=/.?\"\';~`·¨•")

        clean_string = re.sub('[^A-Za-z0-9_À-ÿ ]+','', dirty_string)
        
        return clean_string

    def add_meta_content(self, content, category):
        """Adds additional meta content to the content string"""
        clean_string = ""
        """Add marketing jargon"""
        meta_content="<table style = 'table-striped table-bordered table-hover' responsive='true'><tr><th>Question</th></tr><tr><td>{question}</td></tr><tr><td><strong>Subject Category</strong>: {category}</td></tr></table>"
        clean_string = meta_content.format(question = content, category = category)
        
        return clean_string

    def add_abstract(self, content, set_length):
        content_length = len(content.split())
        print(content_length)

        min = content_length - set_length
        if min > 0:

            start_length = random.randint(0, min)
            end_length = start_length+set_length


            if content_length > set_length:
                excerpt = ' '.join(content.split()[start_length: end_length])
            else:
                return content
            meta_content="<table><tr><th>Abstract</th></tr><tr><td><i>{excerpt}</i></td></tr></table><p>{content}</p>"
            clean_string = meta_content.format(excerpt = excerpt, content = content)
            return clean_string
        else:
            return content


    def generate_title(self, content, title_length, randomize_title):

        content_count = content.split()
        content_count_length = len(content_count)
        #title = ' '.join(content_count[0:title_length])
        #self.logger.info(randomize_title)

        if randomize_title == 0:

            # calculate 75th percentile
            content_count_length = int(round(0.75 * content_count_length))
            title = ' '.join(content_count[content_count_length:][0:title_length])

        if randomize_title == 0.25:

            content_count_length = int(round(0.25 * content_count_length))
            title = ' '.join(content_count[0:content_count_length][0:title_length])

        if randomize_title == 0.5:
            start = int(round(0.25 * content_count_length))
            fin = int(round(0.5 * content_count_length))
            title = ' '.join(content_count[start: fin][0:title_length])

        if randomize_title == 0.75:
            start = int(round(0.5 * content_count_length))
            fin = int(round(0.75 * content_count_length))
            title = ' '.join(content_count[start: fin][0:title_length])

        if randomize_title == 1:
            if content_count_length > (title_length):
                title = ' '.join(content.split()[title_length:(title_length)])
            else:
                title = ' '.join(content.split()[0:-title_length])
        
        if randomize_title == 2:
            if content_count_length > (title_length * 2):
                title = ' '.join(content.split()[title_length:(title_length*2)])
            else:
                title = ' '.join(content.split()[0:-title_length])

        if randomize_title == 3:
            if content_count_length > (title_length * 3):
                title = ' '.join(content.split()[(title_length * 2):(title_length*3)])
            else:
                title = ' '.join(content.split()[0:-title_length])
                
        if randomize_title == 4:
            if content_count_length > (title_length * 4):
                title = ' '.join(content.split()[(title_length * 3):(title_length*4)])
            else:
                title = ' '.join(content.split()[0:-title_length])

        if randomize_title == 5:
            if content_count_length > (title_length * 4):
                title = ' '.join(content.split()[(title_length * 4):(title_length*5)])
            else:
                title = ' '.join(content.split()[0:-title_length])

        if randomize_title == 6:
            if content_count_length > (title_length * 6):
                title = ' '.join(content.split()[(title_length * 5):(title_length*6)])
            else:
                title = ' '.join(content.split()[0:-title_length])
        
        if randomize_title == 7:
            if content_count_length > (title_length * 7):
                title = ' '.join(content.split()[(title_length * 6):(title_length*7)])
            else:
                title = ' '.join(content.split()[0:-title_length])
        
        if randomize_title == 8:
            if content_count_length > (title_length * 8):
                title = ' '.join(content.split()[(title_length * 7):(title_length*8)])
            else:
                title = ' '.join(content.split()[0:-title_length])
        
        if randomize_title == 9:
            if content_count_length > (title_length * 9):
                title = ' '.join(content.split()[(title_length * 8):(title_length*9)])
            else:
                title = ' '.join(content.split()[0:-title_length])
        
        if randomize_title == 10:
            if content_count_length > (title_length * 10):
                title = ' '.join(content.split()[(title_length * 9):(title_length*10)])
            else:
                title = ' '.join(content.split()[0:-title_length])
                
        if randomize_title == -1:
            
            start = int(random.uniform(0, content_count_length))

            self.logger.info(f"Start Position {start} Title Length {title_length} Content count {content_count_length}")
            if (start + title_length) > (content_count_length / 2):
                title = ' '.join(content.split()[-(content_count_length - start + 1) :-title_length])
            else:
                title = ' '.join(content.split()[start:title_length])
        self.logger.info(f"Title choosen: {title}")
        return title

    def add_references_content(self, content):
        content_length = len(content.split())
        limit = 1
        if content_length < 30:
            limit = 1
        if content_length >30 and content_length < 60:
            limit = 1
        if content_length >60 and content_length < 150:
            limit = 2
        if content_length >150:
            limit = 3

        references = fetch_references(self.engine, limit)

        list_string = "<ul>"

        for reference in references:
            list_string = list_string + f"<li>{reference}</li>"
        list_string = list_string + "</ul>"

        meta_content=f"<table style = 'table-striped table-bordered table-hover' responsive='true'><tr><th>Sample references</th></tr><tr><td>{list_string}</td></tr></table>"

        return content + meta_content

    def add_postfix(self, title, postfix):
        return f"{title} {postfix}"

    def add_prefix(self, title, prefix):
        return f"{prefix}  {title}"

    def get_excerpt(self, content):
        content_length = len(content.split())
        if content_length > 45:
            excerpt = ' '.join(content.split()[-45:])
        else:
            excerpt = ' '.join(content.split()[-45:])
        return excerpt
