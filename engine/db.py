# Db Access Class
from mysql.connector.locales.eng import client_error
import mysql.connector
import logging
import socket
#import random

class Db(object):
    """Db access class"""
    def __init__(self, logger = None, connection = None):
        self.logger = logger or logging.getLogger(__name__)
        self.ip = "ip_" + self.get_ip_address()
        if connection is None:
            # in case of development machine
            self.ip = "processed"
        counter = 0
        while counter < 2:
            self.logger.debug("{} : No of connection attempts".format(counter))
            if self.create_connection(connection):
                break
            counter = counter + 1
        self.conn =  False
        self.conn = self.return_connection(self.connection_details)
        self.logger.debug("Database connection created")
        
    def start_conn(self):
        if self.conn is False or None:
            self.conn = self.return_connection(self.connection_details)

    def get_ip_address(self):
        hostname=socket.gethostname()
        return socket.gethostbyname(hostname)
        #return "191.101.130.6" 

    def create_connection(self, connection):
        
        if connection is None:
            self.connection_details = {"host":"localhost", "user":"kush", "password":"incorrect", "database":"crawls", "charset":"utf8"}
        else:
            self.connection_details = connection

    def return_connection(self, connection_details):
        try: 
            connection = mysql.connector.connect(host = connection_details["host"], user = connection_details["user"], passwd = connection_details["password"], db=connection_details["database"], charset="utf8")
        except mysql.connector.Error as err:
            self.logger.error("Error connecting to database", exc_info = 1)
            return False
        else:
            return connection

    
    def fetch_posts(self, month=None,year=None, category=None, posts=None, table=None):
        """method to fetch posts"""
        #create cursor object
        cursor = self.conn.cursor(dictionary=True)
        #create dynamic queries
        # query where category is not specified
        query  = "select link_no, title, content, content_length, category from " + table + " where `{ip}` = 'False' and content_length > 75 limit  %s".format(ip = self.ip)
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
        cursor.close()
        return results
        
        
    
    
    ####----------------------------------------------------
    def fetch_posts_from_tables(self, no_of_posts = None, offset = None, tables = None, content_length = None):

        #create cursor object
        cursor = self.conn.cursor(dictionary=True)

        table_results = {}
        no_of_posts = int(no_of_posts)
        post_no = int(no_of_posts/len(tables))
        offset = int(offset/len(tables))


        for table in tables:
            # fetch random
            if post_no != 0:
                query = "select link_no, title, content, content_length, category from " + table + " where `{ip}` = 'False' and content_length > {content_length} ORDER BY RAND() limit %s offset {offset} ".format(ip = self.ip, offset = offset, content_length = content_length)

                self.logger.info(f"[{query}]")



                self.logger.info((query + ' '+str(post_no)) )

                try:
                    cursor.execute(query, (post_no,))
                    results = cursor.fetchall()
                    fetched_posts = cursor.rowcount

                except Exception:
                    self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
                    fetched_posts = 0

                self.logger.debug("%s fetched from table %s", fetched_posts, table)
            
                post_no = no_of_posts - fetched_posts
                no_of_posts = no_of_posts - fetched_posts
                table_results[table] = results

        cursor.close()
        return table_results


    ####----------------------------------------------------
    def fetch_posts_from_table(self, no_of_posts = None, offset = None,  table_name = None, content_length = None):

        #create cursor object
        cursor = self.conn.cursor(dictionary=True)

       
        no_of_posts = int(no_of_posts)

        query = "select link_no, title, content, content_length, category from " + table_name + " where `{ip}` = 'False' and content_length > {content_length} ORDER BY RAND() limit %s offset {offset} ".format(ip = self.ip, offset = offset, content_length = content_length)

        self.logger.info(f"[{query}]")
        
        self.logger.info((query + ' '+str(no_of_posts)) )

        try:
            cursor.execute(query, (no_of_posts,))
            results = cursor.fetchall()
            fetched_posts = cursor.rowcount

        except Exception:
            self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
            fetched_posts = 0

        self.logger.debug("%s fetched from table %s", fetched_posts, table_name)
            



        cursor.close()

        return results



    ####----------------------------------------------------
    def fetch_category_posts_from_tables(self, no_of_posts = None, offset=None, table_names = None, content_length = None):
        self.logger.debug(table_names)

        #create cursor object
        cursor = self.conn.cursor(dictionary=True)

        table_results = {}
        no_of_posts = int(no_of_posts)
        tables = list(table_names.keys())
        tables = table_names
        post_no = int(no_of_posts/len(tables))
        offset = int(offset/len(tables))


        for table in table_names.keys():
            # fetch random
            if post_no != 0:
                query = "select link_no, title, content, content_length, category from " + table + " where `{ip}` = 'False' and content_length > {content_length} and category in ('"+ "','".join(table_names[table]) + "') ORDER BY RAND() limit {limit} offset {offset}"
                query = query.format(ip = self.ip, limit = post_no, offset = offset, content_length = content_length)

                self.logger.info(query)

                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    fetched_posts = cursor.rowcount

                except Exception:
                    self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
                    fetched_posts = 0

                self.logger.debug("%s fetched from table %s", fetched_posts, table)
            
                post_no = no_of_posts - fetched_posts
                no_of_posts = no_of_posts - fetched_posts
                table_results[table] = results

        cursor.close()
        return table_results
        


    
    ####----------------------------------------------------
    def update_posts(self, post):
        """update fetched posts"""
        cursor = self.conn.cursor()
        query = "insert into published (title, content, link_no, website, table_source) values (%s,%s,%s,%s,%s)"
        # insert post in table
        try:
            cursor.execute(query,(post['title'],post['content'], post['link_no'], post['website'], post['table']))
            query ='update '+ post['table'] +' set `{ip}` = "True" where link_no = %s'.format(ip = self.ip) 
            cursor.execute(query, (post['link_no'],))
            self.conn.commit()
            self.logger.info("Post No: [%s] updated in db", post['link_no'])
            cursor.close()
            return True
        except:
            self.conn.rollback()
            self.logger.warning("Post No: [%s] was not updated to the website due to an insert error", post['link_no'])
            self.logger.error('Problem with update operation', exc_info=True)
            cursor.close()
            return False

        ####----------------------------------------------------
    def update_db_posts(self, post):
        """update fetched posts"""
        cursor = self.conn.cursor()
        query = "insert into published (link_no, website, table_source) values (%s,%s,%s)"
        # insert post in table
        try:
            cursor.execute(query,(post[0],post[1], post[2]))
            query ='update '+ post[2] +' set `{ip}` = "True" where link_no = %s'.format(ip = self.ip) 
            cursor.execute(query, (post[0],))
            self.conn.commit()
            self.logger.info("Post No: [%s] updated in db", post[0])
            cursor.close()
            return True
        except:
            self.conn.rollback()
            self.logger.warning("Post No: [%s] was not updated to the website due to an insert error", post[0])
            self.logger.error('Problem with update operation', exc_info=True)
            cursor.close()
            return False

    def update_multiple_posts(self, posts):
        """Update multiple posts"""
        cursor = self.conn.cursor()
        query ='update '+ posts[0][2] +' set `{ip}` = "True" where link_no = %s'.format(ip = self.ip)
        records_to_update = []
        for post in posts:
            records_to_update.append((post[0],))
            #self.logger.info(records_to_update)
        try:
            cursor.executemany(query, records_to_update)
            self.conn.commit()
            self.logger.info("[%s] posts updated in db", len(posts))
            cursor.close()
            return True
        except:
            self.conn.rollback()
            self.logger.warning("[%s] posts failed to updated in db", len(posts))
            self.logger.error('Problem with update operation', exc_info=True)
            cursor.close()
            return False

    def update_multiple_short_posts(self, posts):
        """Update multiple posts"""
        cursor = self.conn.cursor()
        query ='update '+ posts[0][1] +' set `{ip}` = "True", short = "True" where link_no = %s'.format(ip = self.ip)
        records_to_update = []
        for post in posts:
            records_to_update.append((post[0],))
            #self.logger.info(records_to_update)
        try:
            cursor.executemany(query, records_to_update)
            self.conn.commit()
            self.logger.info("[%s] posts updated in db", len(posts))
            cursor.close()
            return True
        except:
            self.conn.rollback()
            self.logger.warning("[%s] posts failed to updated in db", len(posts))
            self.logger.error('Problem with update operation', exc_info=True)
            cursor.close()
            return False

    def insert_multiple_posts(self, posts):
        cursor = self.conn.cursor()
        query = "insert into published (link_no, website, table_source) values (%s,%s,%s)"
        records_to_update = []
        for post in posts:
            records_to_update.append((post[0],post[1], post[2]))
        try:
            cursor.executemany(query, records_to_update)
            self.conn.commit()
            self.logger.info("[%s] posts inserted in db", len(posts))
            cursor.close()
            return True
        except:
            self.conn.rollback()
            self.logger.warning("[%s] posts failed to insert in db", len(posts))
            self.logger.error('Problem with update operation', exc_info=True)
            cursor.close()
            return False

    def update_short_posts(self, table, post_no):
        """update fetched posts"""
        cursor = self.conn.cursor()
        # update table
        try:
            query = 'update '+ table + ' set `{ip}` = "True",short = "True" where link_no = %s'.format(ip = self.ip)
            cursor.execute(query, (post_no,))
            self.conn.commit()
            self.logger.debug("Post No: [%s] updated in db", post_no)
            cursor.close()
            return True
        except:
            self.conn.rollback()
            self.logger.warning("Post No: [%s] was not updated to the website due to an insert error", post_no)
            self.logger.error('Problem with update operation', exc_info=True)
            cursor.close()
            return False

    def fetch_tables_summary(self):
        query = "SHOW TABLES LIKE '%_content'"
        cursor = self.conn.cursor()
        # run the query

        try:
            cursor.execute(query)
            tables = cursor.fetchall()
            self.logger.debug("Fetching database tables")
        except:
            self.logger.error("Unable to fetch database tabkles")
        cursor.close()
        results = {}

        cursor = self.conn.cursor(dictionary=True)
        for table in tables:
            query = "SELECT count(*) as 'Available Posts' FROM {table} where `{ip}` = 'False' and content_length > 75".format(table = table[0], ip = self.ip)
            #print(query)
            cursor.execute(query)
            result = cursor.fetchall()
            
            summary = "{} - {} posts".format(table[0], result[0]['Available Posts'])
            results [summary]=  table[0]

        cursor.close()
        return results



        


    #########----------------------------
    def fetch_tables(self):
        query = "SHOW TABLES LIKE '%_content'";
        cursor = self.conn.cursor()
        # run the query

        try:
            cursor.execute(query)
            table_names = cursor.fetchall()
            self.conn.commit()
            self.logger.debug("Fetching database tables")
        except:
            self.conn.rollback()
            self.logger.error("Unable to fetch database tabkles")
        return table_names

    
    #####---------------------------------
    def fetch_table_statistics(self):
        # fetch tables 
        tables = self.fetch_tables()


        # for each table fetch published, unpublished, rejected, crawled, links
        table_statistics = []
        for table in tables:
            links_table = table[0].split("_")
            links_table[-1] = "links"
            links_table = ("_").join(links_table)

            query = """
             SELECT count(*) FROM {table} where `{ip}` = 'True'
             union all
             SELECT count(*) FROM {table} where `{ip}` = 'False'
             union all
             SELECT count(*) FROM {table} where short = 'True'
             union all
             Select count(*) from {table}
             union all
             Select count(*) from {links_table}

             """.format(table = table[0], links_table = links_table, ip = self.ip)
            results = self.process_query(query)
            stats = [table[0]]
            for row in results:
                stats.append(row[0])
            table_statistics.append(stats)
        return table_statistics


    def fetch_category_statistics(self, table_list):

        category_statistics = {}

        for table in table_list:
            query = """
            SELECT count(*), category, `{ip}` FROM {table} where content_length >75 group by category, `{ip}`""".format(table = table, ip = self.ip)
            results = self.process_query(query)
            category_statistics[table] = results

        
        return category_statistics


    def process_query(self, query):
        print(query)

        cursor = self.conn.cursor()
        # run the query

        results = []

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            self.logger.debug("Processing query")
        except:
            self.logger.error("Unable to fetch database tables")
        return results

    #------------------------------------------------------------

    def fetch_total_tables_summary(self):
        query = "SHOW TABLES LIKE '%_content'"
        cursor = self.conn.cursor()
        # run the query

        try:
            cursor.execute(query)
            tables = cursor.fetchall()
            self.logger.debug("Fetching database tables")
        except:
            self.logger.error("Unable to fetch database tabkles")
        cursor.close()
        results = {}

        cursor = self.conn.cursor(dictionary=True)
        for table in tables:
            query = "SELECT count(*) as 'Available Posts' FROM {table}".format(table = table[0])
            
            cursor.execute(query)
            result = cursor.fetchall()
            
            summary = "{} - {} posts".format(table[0], result[0]['Available Posts'])
            results [summary]=  table[0]

        cursor.close()
        return results

    ####----------------------------------------------------
    def fetch_all_posts_from_table(self, no_of_posts = None, offset = None,  table_name = None, content_length = None):

        #create cursor object
        cursor = self.conn.cursor(dictionary=True)

       
        no_of_posts = int(no_of_posts)

        query = "select link_no, title, content, content_length, category from " + table_name + " where LENGTH(content) - LENGTH(REPLACE(content, ' ', '')) > {content_length} ORDER BY date_recorded asc limit %s offset {offset} ".format( offset = offset, content_length = content_length)

        self.logger.info(f"[{query}]")
        
        self.logger.info((query + ' '+str(no_of_posts)) )

        try:
            cursor.execute(query, (no_of_posts,))
            results = cursor.fetchall()
            fetched_posts = cursor.rowcount

        except Exception:
            self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
            fetched_posts = 0

        self.logger.debug("%s fetched from table %s", fetched_posts, table_name)
            



        cursor.close()

        return results

        ####----------------------------------------------------
    def fetch_available_posts(self, table_name = None, content_length = None):
        cursor = self.conn.cursor(dictionary=True)

       

        query = "select count(*) as count from " + table_name + " where LENGTH(content) - LENGTH(REPLACE(content, ' ', '')) > {content_length} ".format(  content_length = content_length)

        self.logger.info(f"[{query}]")


        try:
            cursor.execute(query)
            results = cursor.fetchall()
            fetched_posts = cursor.rowcount

        except Exception:
            self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
            fetched_posts = 0

        self.logger.debug("%s fetched from table %s", fetched_posts, table_name)
            



        cursor.close()
        print(results)

        return results



                
    def close_conn(self):
        self.conn.close()
        self.conn = False
    