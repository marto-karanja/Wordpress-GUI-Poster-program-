import logging
import time
from engine.cleaner import Cleaner
from engine.db import Db
from engine.post import WpPost



class Posta():
    """main class"""
    def __init__(self, settings, logger = None):
        self.settings = settings
        # get logger object
        self.logger = logger or logging.getLogger(__name__)
        
        return
    def main(self):
        """main method"""
        # get settings object
        for item in self.settings['workload']:
            self.logger.info("[%s]: attempting to post %s %s posts", item['site'],item['posts'], item['category'])
            self.post_content(item)
        
        
    
    def post_content(self, workload):
        """main method"""
        # initialize DB class
        db = Db()
        self.logger.debug("Finished setting up database connection")
        # initialize posting class
        site = WpPost(workload['site'] +'/xmlrpc.php', 'kush', 'incorrect0727531915')
        # initialize cleaner
        cleaner = Cleaner()
        posts = db.fetch_posts( posts = workload['posts'], table = workload['table'] )

        short_content = []
        # itearate through posts 
        for post in posts:
            # clean post
            # check if content is long enough
            self.logger.debug("Cleaning content: %s", post['link_no'])
            content = cleaner.clean_content(post['content'])
            if content:
                self.logger.debug("Cleaning title: %s", post['link_no'])
                title = cleaner.clean_title(post['title'])
                category = [post['category']]
                """Add meta content"""
                content = cleaner.add_meta_content(content, category)
                # post
                site.publish_post(title, content, category)
                self.logger.info("Post No: [%s] published", post['link_no'])
                # slow down script for one minute to reduce hitting server rate limiter
                time.sleep(100)
                self.logger.info("Script paused execution for 60 secs")
                # update published table
                published = {}
                published['title'] = title
                published['content'] = content
                published['link_no'] = post['link_no']
                published['website'] = workload['site']
                published['table'] = workload['table']
                # update db records
                db.update_posts(published)
                self.logger.debug("Post No: [%s] published and updated", post['link_no'])
            else:
                # update the short content strings on the db
                self.logger.debug("Updating short record string:[%s]",post['link_no'])
                db.update_short_posts(workload['table'], post['link_no'])
                # update short content
                short_content.append(post['link_no'])
        self.logger.info("%s short posts found out of %s", (len(short_content)), workload['posts'])
        # Log short content length
        self.logger.info("****Rejected Short Posts****",)
        for no in short_content:
            self.logger.info("Link No: [%s]",no)
        db.close_conn()
        self.logger.info("Closing database connection")
        return