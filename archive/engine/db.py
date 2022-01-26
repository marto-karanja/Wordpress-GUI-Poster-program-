# Db Access Class
import mysql.connector
import logging

class Db(object):
    """Db access class"""
    def __init__(self, logger = None):
        self.conn = mysql.connector.connect(host="localhost", user="kush", passwd="incorrect", db="crawls", charset="utf8")
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Database connection created")
    
    def fetch_posts(self, month=None,year=None, category=None, posts=None, table=None):
        """method to fetch posts"""
        #create cursor object
        cursor = self.conn.cursor(dictionary=True)
        #create dynamic queries
        # fetch from different databases
        #query  = "select link_no, title, processed_content, category from " + table + " where category=%s and processed = 'False' limit %s"
        # query where category is not specified
        query  = "select link_no, title, content, category from " + table + " where processed = 'False' limit %s"
        self.logger.info((query + ' '+str(int(posts))) )
        try:
            cursor.execute(query, (int(posts),))
            results = cursor.fetchall()
        except Exception:
            self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
            fetched_posts = 0
        # get the results as a python dictionary
        fetched_posts = cursor.rowcount
        self.logger.info("Fetched %s posts", fetched_posts)
        return results
    
    def update_posts(self, post):
        """update fetched posts"""
        cursor = self.conn.cursor()
        query = "insert into published (title, content, link_no, website, table_source) values (%s,%s,%s,%s,%s)"
        # insert post in table
        try:
            cursor.execute(query,(post['title'],post['content'], post['link_no'], post['website'], post['table']))
            query ='update '+ post['table'] +' set processed = "True" where link_no = %s' 
            cursor.execute(query, (post['link_no'],))
            self.conn.commit()
            self.logger.info("Post No: [%s] updated in db", post['link_no'])
            return True
        except:
            self.conn.rollback()
            self.logger.warning("Post No: [%s] was not updated to the website due to an insert error", post['link_no'])
            self.logger.error('Problem with update operation', exc_info=True)
            return False

    def update_short_posts(self, table, post_no):
        """update fetched posts"""
        cursor = self.conn.cursor()
        # update table
        try:
            query = 'update '+ table + ' set processed = "True",short = "True" where link_no = %s'
            cursor.execute(query, (post_no,))
            self.conn.commit()
            self.logger.debug("Post No: [%s] updated in db", post_no)
            return True
        except:
            self.conn.rollback()
            self.logger.warning("Post No: [%s] was not updated to the website due to an insert error", post_no)
            self.logger.error('Problem with update operation', exc_info=True)
            return False

    def fetch_tables(self):
        query = "SHOW TABLES LIKE '%_content'";
        cursor = self.conn.cursor()
        # run the query

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            self.conn.commit()
            self.logger.debug("Fetching database tables")
        except:
            self.conn.rollback()
            self.logger.error("Unable to fetch database tabkles")
        return results
                
    def close_conn(self):
        self.conn.close()
    