import logging
import wx
import time
import threading
import random

import datetime
from datetime import datetime
from engine.cleaner import Cleaner
from engine.db import Db
from engine.post import WpPost
from engine.rest_post import RestPost
from engine.local_db import connect_to_db, create_session, remove_session, save_published_posts, save_short_posts, get_title_length, count_published_posts, get_content_length
from engine.models import PublishedPosts
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session



class Posta():
    """main class"""
    def __init__(self, settings = None, logger = None):
        self.settings = settings
        #self.delay = 15
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
        site = WpPost(workload['site'] +'xmlrpc.php', workload['username'], workload['password'])
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
                time.sleep(2)
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
                self.logger.debug("Short string detected and updated in database[%s]",post['link_no'])
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

    def get_current_time(self):
        now = datetime.now()
        return now.strftime("%H:%M:%S")


    def post_threaded_content(self, workload, thread_queue, event, window):
        """main method"""

        #thread_start = self.get_current_time()

        # Dictionary to store results
        results = {}
        results['Thead start time'] = self.get_current_time()
        thread_name = threading.currentThread().getName()

        # switch to storing published posts in local database
        db = Db()

        
        self.logger.debug("Finished setting up database connection for %s", workload['site'])
        msg = "{}:[{}] added to queue [{}]".format(self.get_current_time(), workload['site'], thread_name)
        self.update_window_reports(window, msg)
        
        # initialize posting class
        site = WpPost(workload['site'] +'xmlrpc.php', workload['username'], workload['password'])
        # initialize cleaner
        cleaner = Cleaner()
        #### To Do
        ## Modify posts fetching function to return dictionary of multiple tables
        posts = db.fetch_posts_from_tables( no_of_posts = workload['posts'], tables = workload['table'] )

        # update GUI grid
        #self.update data grid
        
        short_content = []
        published_posts = []
        # itearate through posts
        total_fetched_posts = 0
        for table,contents in posts.items():
            total_fetched_posts = total_fetched_posts + len(contents)
            for count, post in enumerate(contents):
                # clean post
                # check if content is long enough
                self.logger.debug("Content length: [%s]", post['content_length'])
                
                if not event.isSet():
                    
                    
                    current_time = self.get_current_time()

                    self.logger.debug("Cleaning content: %s", post['link_no'])
                    content = cleaner.clean_content(post['content'])
                    if content:
                        self.update_gui(window, "{}: [{}-{}] Beginning processing post {} of {}. Post length {}. {} remaining".format(self.get_current_time(), threading.currentThread().getName(), workload['site'], count + 1, len(contents), post['content_length'], len(contents)-count-1))
                        self.logger.debug("Cleaning title: %s", post['link_no'])
                        title = ' '.join(content.split()[0:25])
                        #title = cleaner.clean_title(post['title'])
                        category = [post['category']]
                        """Add meta content"""
                        content = cleaner.add_meta_content(content, category)
                        # post
                        if site.publish_post(title, content, category):
                            
                            self.logger.info("Post No: [%s] published", post['link_no'])
                            # slow down script for one minute to reduce hitting server rate limiter

                            
                            # update published table
                            published = {}
                            published['title'] = title
                            published['content'] = content
                            published['link_no'] = post['link_no']
                            published['website'] = workload['site']
                            
                            published['table'] = table

                            # append to published list
                            published_posts.append(post['link_no'])

                            # update db records
                            db.update_posts(published)
                            
                            
                            msg = "{}: Post No: [{}] published and updated to [{}] - [Thread: {}]".format(self.get_current_time(), post['link_no'],published['website'], threading.currentThread().getName())
                            self.update_gui(window, msg )
                            self.logger.debug(msg)
                            delay = random.randint(0, self.delay)
                            self.logger.info("Script paused execution for {} secs".format(delay))
                            self.update_gui(window, "[{}] Script paused execution for {} secs".format(threading.currentThread().getName(), delay))
                            time.sleep(delay)
                        else:
                            self.logger.debug("Failed to publish [%s] to [%s]", post['link_no'], workload['site'])
                            
                            msg = "{}: Post No: [{}] failed to publish [{}] - [Thread: {}]".format(self.get_current_time(), post['link_no'],workload['site'], threading.currentThread().getName())
                            self.update_gui(window, msg )

                    else:
                        # update the short content strings on the db
                        self.update_gui(window, "{}: Short string. Failed to publish [{}]. {} posts remaining".format(self.get_current_time(), post['link_no'], len(contents)-count-1))
                        #self.update_gui(window, "{}: Updating short record string:[{}]".format(current_time, post['link_no']))
                        self.logger.debug("Updating short record string:[%s]",post['link_no'])
                        db.update_short_posts(table, post['link_no'])
                        # update short content
                        short_content.append(post['link_no'])
                
                else:
                    self.update_gui(window, "Stopping thread [{}]".format(threading.currentThread().getName()))
                    # break out of loop
                    break


        self.logger.info("%s short posts found out of %s", (len(short_content)), workload['posts'])
        results['Short Posts'] = short_content
        results['Website'] = workload['site']
        results['Thread Name'] = thread_name
        results ['Posts Published'] = published_posts
        thread_completion = datetime.now()
        thread_completion = thread_completion.strftime("%H:%M:%S")
        results ['Thread Completion Time'] = thread_completion

        thread_queue.put(results)

        # print out reports
        self.update_window_reports(window, "**************************")
        self.update_window_reports(window, "{}: Thread Completed [{}]".format(self.get_current_time(), thread_name))
        self.update_window_reports(window, "{}: [{}] Short posts [{}][{}]".format(self.get_current_time(), len(short_content),thread_name, workload['site']))
        self.update_window_reports(window, "{}: [{}] Posts published [{}][{}]".format(self.get_current_time(), len(published_posts),thread_name, workload['site']))
        self.update_window_reports(window, "{}: [{}] Posts failed to publish [{}][{}]".format(self.get_current_time(), total_fetched_posts - len(published_posts),thread_name, workload['site']))
        self.update_window_reports(window, "**************************")
        # Log short content length
  
        db.close_conn()
        self.logger.info("Closing database connection")
        return

    def post_content_rest_method(self, connection, Session, publishing_date, delay, posts, workload, thread_queue, event, window ):

        session = Session()

        self.delay = delay
        results = {}
        results['Thead start time'] = self.get_current_time()
        thread_name = threading.currentThread().getName()
        
        # initialize posting class
        site = RestPost(workload['site'], workload['username'], workload['application_password'], self.logger)
        # initialize cleaner
        cleaner = Cleaner()

        title_length = int(get_title_length(session))
        content_length = int(get_content_length(session))

        # switch to storing published posts in local sqllite database
        # fetch engine, create session


        
        self.logger.debug("Finished setting up database connection for %s", workload['site'])
        msg = "{}:[{}] added to queue [{}]".format(self.get_current_time(), workload['site'], thread_name)
        self.update_window_reports(window, msg)

        
        short_content = []
        published_posts = []
        # itearate through posts
        total_fetched_posts = 0
        for table,contents in posts.items():
            total_fetched_posts = total_fetched_posts + len(contents)
            for count, post in enumerate(contents):
                # clean post
                # check if content is long enough
                self.logger.debug("Content length: [%s]", post['content_length'])
                
                if not event.isSet():
                    
                    
                    #current_time = self.get_current_time()

                    self.logger.debug("Cleaning content: %s", post['link_no'])
                    content = cleaner.clean_content(post['content'], content_length)
                    if content:

                        #print(content)


                        self.update_gui(window, "{}: [{}-{}] Beginning processing post {} of {}. Post length {}. {} remaining".format(self.get_current_time(), threading.currentThread().getName(), workload['site'], count + 1, len(contents), post['content_length'], len(contents)-count-1))
                        self.logger.debug("Cleaning title: %s", post['link_no'])
                        title = ' '.join(content.split()[0:title_length])


                        if window.abstract_checkbox.GetValue():
                            content = cleaner.add_abstract(content)

                        #self.logger.info(content)
                        #title = cleaner.clean_title(post['title'])
                        category = [post['category']]
                        """Add meta content"""
                        content = cleaner.add_meta_content(content, category)
                        # post
                        if site.publish_post(title, content, category, publishing_date):
                            
                            self.logger.info("Post No: [%s] published", post['link_no'])
                            # slow down script for one minute to reduce hitting server rate limiter

                            
                            # update published table
                            published = PublishedPosts()
                            published.title = title
                            published.content = content
                            published.link_no = post['link_no']
                            published.website = workload['site']
                            
                            published.table = table

                            # append to published list
                            published_posts.append(post['link_no'])

                            # update db records
                            try:
                                save_published_posts(session, published)
                            except Exception as e:
                                msg = "{}: Post No: [{}] was not stored in the database - [Thread: {}]".format(self.get_current_time(), post['link_no'], threading.currentThread().getName())
                                self.update_gui(window, msg )
                                self.logger.error(msg, exc_info=1)
                            else:
                                #db.update_posts(published)
                                msg = "{}: Post No: [{}] published and updated to [{}] - [Thread: {}]".format(self.get_current_time(), post['link_no'],published.website, threading.currentThread().getName())
                                self.update_gui(window, msg )
                                self.logger.debug(msg)
                            delay = random.randint(int(self.delay/2), int(self.delay))
                            self.logger.info("Script paused execution for {} secs".format(delay))
                            self.update_gui(window, "[{}] Script paused execution for {} secs".format(threading.currentThread().getName(), delay))

                            # update count in main window
                            window.update_post_count = str(count_published_posts(session))
                            window.updated_posts_label.SetLabel(f"{window.update_post_count} posts need to be updated")
                            
                            time.sleep(delay)
                        else:
                            self.logger.debug("Failed to publish [%s] to [%s]", post['link_no'], workload['site'])
                            
                            msg = "{}: Post No: [{}] failed to publish [{}] - [Thread: {}]".format(self.get_current_time(), post['link_no'],workload['site'], threading.currentThread().getName())
                            self.update_gui(window, msg )

                    else:
                        # update the short content strings on the db
                        msg = "{}: Short string. Failed to publish [{}]. {} posts remaining".format(self.get_current_time(), post['link_no'], len(contents)-count-1)
                        self.update_gui(window, msg)
                        #self.update_gui(window, "{}: Updating short record string:[{}]".format(current_time, post['link_no']))
                        
                        #db.update_short_posts(table, post['link_no'])
                        # update short content


                        # save_short_posts(session, post['link_no'])

                        short_content.append(post['link_no'])
                        # update short content in database

                        try:
                            save_short_posts(Session(), post['link_no'], table)
                        except Exception as e:
                            msg = "{}: Short Post No: [{}] was not stored in the database - [Thread: {}]".format(self.get_current_time(), post['link_no'], threading.currentThread().getName())
                            self.update_gui(window, msg )
                            self.logger.error(msg, exc_info=1)
                        else:
                            msg = "{}: Short string. updated in database [{}].".format(self.get_current_time(), post['link_no'])
                            self.update_gui(window, msg )
                            self.logger.debug("Updating short record string:[%s]",post['link_no'])

                
                else:
                    self.update_gui(window, "Stopping thread [{}]".format(threading.currentThread().getName()))
                    # break out of loop
                    break         


        self.update_gui(window, "*******************************************************")
        self.logger.info("%s short posts found out of %s", (len(short_content)), workload['posts'])
        results['Short Posts'] = short_content
        results['Website'] = workload['site']
        results['Thread Name'] = thread_name
        results ['Posts Published'] = published_posts
        thread_completion = datetime.now()
        thread_completion = thread_completion.strftime("%H:%M:%S")
        results ['Thread Completion Time'] = thread_completion

        thread_queue.put(results)

        # print out reports
        self.update_window_reports(window, "**************************")
        self.update_window_reports(window, "{}: Thread Completed [{}]".format(self.get_current_time(), thread_name))
        self.update_window_reports(window, "{}: [{}] Short posts [{}][{}]".format(self.get_current_time(), len(short_content),thread_name, workload['site']))
        self.update_window_reports(window, "{}: [{}] Posts published [{}][{}]".format(self.get_current_time(), len(published_posts),thread_name, workload['site']))
        self.update_window_reports(window, "{}: [{}] Posts failed to publish [{}][{}]".format(self.get_current_time(), total_fetched_posts - len(published_posts),thread_name, workload['site']))
        self.update_window_reports(window, "**************************")
        # Log short content length

        Session.remove()
  
        #db.close_conn()
        #self.logger.info("Closing database connection")
        #event.set()
        return


    def post_category_rest_method(self, connection,Session, publishing_date, delay, posts, workload, thread_queue, event, window, categories ):
        session = Session()

        self.delay = delay
        results = {}
        results['Thead start time'] = self.get_current_time()
        thread_name = threading.currentThread().getName()

        if connection is None:
            db = Db()
        else:
            db = Db(connection = connection)
        
        # initialize posting class
        site = RestPost(workload['site'], workload['username'], workload['application_password'], self.logger)
        # initialize cleaner
        cleaner = Cleaner()

        
        self.logger.debug("Finished setting up database connection for %s", workload['site'])
        msg = "{}:[{}] added to queue [{}]".format(self.get_current_time(), workload['site'], thread_name)
        self.update_window_reports(window, msg)

        title_length = int(get_title_length(session))
        content_length = int(get_content_length(session))


        # update GUI grid
        #self.update data grid
        
        short_content = []
        published_posts = []
        # itearate through posts
        total_fetched_posts = 0
        for table,contents in posts.items():
            total_fetched_posts = total_fetched_posts + len(contents)
            for count, post in enumerate(contents):
                # clean post
                # check if content is long enough
                self.logger.debug("Content length: [%s]", post['content_length'])
                
                if not event.isSet():
                    
                    
                    #current_time = self.get_current_time()

                    self.logger.debug("Cleaning content: %s", post['link_no'])
                    content = cleaner.clean_content(post['content'], content_length)

                    if content:

                        self.update_gui(window, "{}: [{}-{}] Beginning processing post {} of {}. Post length {}. {} remaining".format(self.get_current_time(), threading.currentThread().getName(), workload['site'], count + 1, len(contents), post['content_length'], len(contents)-count-1))
                        self.logger.debug("Cleaning title: %s", post['link_no'])

                        title = ' '.join(content.split()[0:title_length])
                        #title = cleaner.clean_title(post['title'])
                        category = [post['category']]
                        """Add meta content"""
                        content = cleaner.add_meta_content(content, category)

                        if window.abstract_checkbox.GetValue():
                            content = cleaner.add_abstract(content)


                        # post
                        if site.publish_post(title, content, category, publishing_date):
                            
                            self.logger.info("Post No: [%s] published", post['link_no'])
                            # slow down script for one minute to reduce hitting server rate limiter

                            
                            # update published table
                            published = PublishedPosts()
                            published.title = title
                            published.content = content
                            published.link_no = post['link_no']
                            published.website = workload['site']
                            
                            published.table = table

                            # append to published list
                            published_posts.append(post['link_no'])
                            
                            # update db records
                            try:
                                save_published_posts(session, published)
                            except Exception as e:
                                msg = "{}: Post No: [{}] was not stored in the database - [Thread: {}]".format(self.get_current_time(), post['link_no'], threading.currentThread().getName())
                                self.update_gui(window, msg )
                                self.logger.error(msg, exc_info=1)
                            else:
                                #db.update_posts(published)
                                msg = "{}: Post No: [{}] published and updated to [{}] - [Thread: {}]".format(self.get_current_time(), post['link_no'],published.website, threading.currentThread().getName())
                                self.update_gui(window, msg )
                                self.logger.debug(msg)
                            delay = random.randint(int(self.delay/2), int(self.delay))
                            self.logger.info("Script paused execution for {} secs".format(delay))
                            self.update_gui(window, "[{}] Script paused execution for {} secs".format(threading.currentThread().getName(), delay))
                            # update count in main window
                            window.update_post_count = str(count_published_posts(session))
                            window.updated_posts_label.SetLabel(f"{window.update_post_count} posts need to be updated")
                            time.sleep(delay)
                        else:
                            self.logger.debug("Failed to publish [%s] to [%s]", post['link_no'], workload['site'])
                            
                            msg = "{}: Post No: [{}] failed to publish [{}] - [Thread: {}]".format(self.get_current_time(), post['link_no'],workload['site'], threading.currentThread().getName())
                            self.update_gui(window, msg )

                    else:
                        # update the short content strings on the db
                        self.update_gui(window, "{}: Short string. Failed to publish [{}]. {} posts remaining".format(self.get_current_time(), post['link_no'], len(contents)-count-1))
                        #self.update_gui(window, "{}: Updating short record string:[{}]".format(current_time, post['link_no']))
                        self.logger.debug("Updating short record string:[%s]",post['link_no'])

                        short_content.append(post['link_no'])
                        try:
                            save_short_posts(Session(), post['link_no'])
                        except Exception as e:
                            msg = "{}: Short Post No: [{}] was not stored in the database - [Thread: {}]".format(self.get_current_time(), post['link_no'], threading.currentThread().getName())
                            self.update_gui(window, msg )
                            self.logger.error(msg, exc_info=1)
                        else:
                            msg = "{}: Short string. updated in database [{}].".format(self.get_current_time(), post['link_no'])
                            self.update_gui(window, msg )
                            self.logger.debug("Updating short record string:[%s]",post['link_no'])

                
                else:
                    self.update_gui(window, "Stopping thread [{}]".format(threading.currentThread().getName()))
                    # break out of loop
                    break         


        self.update_gui(window, "*******************************************************")
        self.logger.info("%s short posts found out of %s", (len(short_content)), workload['posts'])
        results['Short Posts'] = short_content
        results['Website'] = workload['site']
        results['Thread Name'] = thread_name
        results ['Posts Published'] = published_posts
        thread_completion = datetime.now()
        thread_completion = thread_completion.strftime("%H:%M:%S")
        results ['Thread Completion Time'] = thread_completion

        thread_queue.put(results)

        # print out reports
        self.update_window_reports(window, "**************************")
        self.update_window_reports(window, "{}: Thread Completed [{}]".format(self.get_current_time(), thread_name))
        self.update_window_reports(window, "{}: [{}] Short posts [{}][{}]".format(self.get_current_time(), len(short_content),thread_name, workload['site']))
        self.update_window_reports(window, "{}: [{}] Posts published [{}][{}]".format(self.get_current_time(), len(published_posts),thread_name, workload['site']))
        self.update_window_reports(window, "{}: [{}] Posts failed to publish [{}][{}]".format(self.get_current_time(), total_fetched_posts - len(published_posts),thread_name, workload['site']))
        self.update_window_reports(window, "**************************")
        # Log short content length
  
        Session.remove()
        #db.close_conn()
        #self.logger.info("Closing database connection")
        return


    def update_gui(self, window, msg):
        wx.CallAfter(window.log_message_to_txt_field,msg )

    def update_window_reports(self, window, msg):
        wx.CallAfter(window.log_message_to_report_txt_field,msg )