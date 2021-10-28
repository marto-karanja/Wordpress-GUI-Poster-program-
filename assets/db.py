import mysql.connector
import logging

class Db(object):
    """Wrapper class to access DB"""
    def __init__(self, logger = None):
        self.conn = mysql.connector.connect(host="localhost", user="kush", passwd="incorrect", db="crawls", charset="utf8")
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Database connection created")

    def execute_query(self, query):
        """Executes query and returns data"""
        #create cursor object
        cursor = self.conn.cursor(dictionary=True)
        self.logger.info("[Executing query]: %s",query)
        try:
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception:
            self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
            fetched_posts = 0
        # get the results as a python dictionary
        fetched_posts = cursor.rowcount
        self.logger.info("Query Fetched %s posts", fetched_posts)
        return results
