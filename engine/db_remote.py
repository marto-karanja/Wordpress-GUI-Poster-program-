# Db Access Class
from mysql.connector.locales.eng import client_error
import random
import mysql.connector
from datetime import datetime
import logging
import socket
import paramiko
import os
import string
import sshtunnel
import wx



from functools import wraps

logger = logging.getLogger(__name__)


def db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Open MySQL connection
        self = args[0]
        sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG

        #ssh_password = "incorrect0727531915"


        security_key = paramiko.RSAKey.from_private_key_file(self.connection_details.security_filepath, self.connection_details.ssh_password)

        sshtunnel.SSH_TIMEOUT = 6000.0
        sshtunnel.TUNNEL_TIMEOUT = 12000.0

        tunnel = sshtunnel.SSHTunnelForwarder(
                (self.connection_details.ssh_host, int(self.connection_details.ssh_port)),
                ssh_private_key=security_key,
                ssh_username = self.connection_details.cpanel_username,
                set_keepalive = 12000,
                remote_bind_address = ('127.0.0.1', 3306)
            )
        try:
            tunnel.start()
        except Exception as e:
            logger.error(f"A connection error has occured", str(e))
            frame = wx.Frame(None)
            wx.MessageBox("Error connecting to websites database", "Error!", wx.OK|wx.ICON_INFORMATION|wx.STAY_ON_TOP, frame, 120)
            frame.Destroy()
            return None
        
        try:
            conn = connect_to_mysql(tunnel, self.connection_details)
        except Exception as e:
            logger.error("Error connecting to MySQL server:", str(e))
            frame = wx.Frame(None)
            wx.MessageBox("Error connecting to websites database", "Error!", wx.OK|wx.ICON_INFORMATION|wx.STAY_ON_TOP, frame, 120)
            frame.Destroy()
            tunnel.close()
            return None


        # Call the function and store the result
        result = func(conn, *args, **kwargs)

        # Close MySQL connection
        conn.close()
        tunnel.close()

        # Return the result
        return result

    return wrapper
    



def connect_to_mysql(tunnel, connection_details):
    # Connect to a MySQL server using the SSH tunnel connection
    try:
        conn = mysql.connector.MySQLConnection(
            host = '127.0.0.1',
            user = connection_details.database_username,
            passwd = connection_details.database_password,
            db = connection_details.database_name,
            port=tunnel.local_bind_port,
            use_pure=True,
            charset='utf8',
            use_unicode=True
    )
    except Exception as e:
        
        logger.error(f"A connection error has occured", str(e))
        raise e
    
        
    else:
        logger.info("Successfully connected to remote database")
    
    return conn






class Db(object):
    """Db access class"""

    def __init__(self, logger = None, connection_details = None):

        self.connection_details = connection_details

        self.logger = logger or logging.getLogger(__name__)

        self.connection_attempts = 1

        self.connection = None

    def start_conn(self):
        self.open_ssh_tunnel()

        self.connect_to_mysql()
        


    def connect_to_mysql(self):
        # Connect to a MySQL server using the SSH tunnel connection
        try:
            self.connection = mysql.connector.MySQLConnection(
            host = '127.0.0.1',
            user = self.connection_details.database_username,
            passwd = self.connection_details.database_password,
            db = self.connection_details.database_name,
            port=self.tunnel.local_bind_port,
            use_pure=True,
            charset='utf8',
            use_unicode=True
        )
        except Exception as e:
            self.logger.info(f"A connection error has occured")
            if self.connection_attempts <= 3:
                self.logger.info(f"Connection attempt: {self.connection_attempts}")

                self.connection_attempts = self.connection_attempts + 1

                frame = wx.Frame(None)

                wx.MessageBox("Error connecting to websites database", "Error!", wx.OK|wx.ICON_INFORMATION|wx.STAY_ON_TOP, frame, 120)
                
                frame.Destroy()

                self.open_ssh_tunnel()
                self.connect_to_mysql()
            else:
                self.logger.info(f"Unable to connect to db after multiple attempts")
        
            
        else:
            self.logger.info("Successfully connected to remote database")
            
        
        



    def open_ssh_tunnel(self, verbose=False):
        """Open an SSH tunnel and connect using a username and password.
        
        :param verbose: Set to True to show logging
        :return tunnel: Global SSH tunnel connection

         """

        
        if verbose:
            sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG


        #security_key = paramiko.RSAKey.from_private_key_file((os.getcwd() +"\\key\\buyapcan_key"),ssh_password) 
        security_key = paramiko.RSAKey.from_private_key_file(self.connection_details.security_filepath, self.connection_details.ssh_password)

        sshtunnel.SSH_TIMEOUT = 6000.0
        sshtunnel.TUNNEL_TIMEOUT = 12000.0
        try:


            self.tunnel = sshtunnel.SSHTunnelForwarder(
                    (self.connection_details.ssh_host, int(self.connection_details.ssh_port)),
                    ssh_private_key=security_key,
                    ssh_username = self.connection_details.cpanel_username,
                    set_keepalive = 12000,
                    remote_bind_address = ('127.0.0.1', 3306)
                )
                
            self.tunnel.start()
        except Exception as e:
            self.logger.error("An error has occured", exc_info=1)
            frame = wx.Frame(None)
            wx.MessageBox("Error connecting to websites database", "Error!", wx.OK|wx.ICON_INFORMATION|wx.STAY_ON_TOP, frame, 120)
            frame.Destroy()

    def run_query(self):
        """method to fetch posts"""
        #create cursor object
        cursor = self.connection.cursor(dictionary=True)
        #create dynamic queries
        # query where category is not specified
        query  = f"select * from {self.connection_details.table_prefix}_posts limit  100"

        self.logger.info(query)

        try:
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception:

            self.logger.debug("[ERROR STRING]:%s", cursor._last_executed)
            fetched_posts = 0
        # get the results as a python dictionary
        fetched_posts = cursor.rowcount
        print(fetched_posts)
        self.logger.info("Fetched %s posts", fetched_posts)
        cursor.close()
        print(results)
        return results
    

    def insert_multiple_posts(self, records_to_update, window):
            
        if self.connection is None:
            return None
        # get publishing date
        
        cursor = self.connection.cursor()
        query = f"INSERT INTO {self.connection_details.table_prefix}_posts (`post_title`, `post_name`, `post_content`, `post_excerpt`, `post_status`, `comment_status`, `post_date`, `post_date_gmt`, `post_modified`,`post_modified_gmt`,`guid`, `post_author`,`to_ping`, `pinged` ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, %s,%s,%s,'','')"
        
        try:
            cursor.executemany(query, records_to_update)
            self.connection.commit()
            x = len(records_to_update)
                                
        except ConnectionAbortedError as e:
            self.logger.error("A connection error has occured", exc_info = True)
            window.update_gui("A connection error has occured")
            self.connection.rollback()
            self.logger.warning("[%s] posts failed to insert in db", len(records_to_update))
            window.update_gui("Problem publishing posts to database")
            cursor.close()
            return False
        else:
            self.logger.info("[%s] posts inserted in db", x)
            window.update_gui(f"[{x}] posts inserted in website database")
            # update post category
            #guids = [record[-2] for record in records_to_update]
            #self.update_post_category(guids, cursor = cursor, window= window)
            return True
        finally:
            cursor.close()

    

    @db_connection
    def bulk_insert_posts(conn, self, records_to_update, window):
            
        if conn is None:
            return None
        # get publishing date
        
        cursor = conn.cursor()
        query = f"INSERT INTO {self.connection_details.table_prefix}_posts (`post_title`, `post_name`, `post_content`, `post_excerpt`, `post_status`, `comment_status`, `post_date`, `post_date_gmt`, `post_modified`,`post_modified_gmt`,`guid`, `post_author`, `to_ping`, `pinged`,`post_content_filtered`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, %s,%s,%s, '', '','')"

        window.update_gui(f"Attempting to insert {len(records_to_update)} to database")
        
        try:
            cursor.executemany(query, records_to_update)
            conn.commit()
            x = len(records_to_update)
                                
        except ConnectionAbortedError as e:
            self.logger.error("A connection error has occured", exc_info = True)
            window.update_gui("A connection error has occured")
            conn.rollback()
            self.logger.warning("[%s] posts failed to insert in db", len(records_to_update))
            window.update_gui("Problem publishing posts to database")
            return False
        except Exception as e:
            self.logger.error("An error has occured", exc_info = True)
            window.update_gui("An error has occured")
            conn.rollback()
            window.update_gui("Problem publishing posts to database")
            return False

        else:
            self.logger.info("[%s] posts inserted in db", x)
            window.update_gui(f"[{x}] posts inserted in website database")
            return True
        finally:
            cursor.close()



    def update_post_category(self, guids, cursor, window):
        #cursor = self.connection.cursor(dictionary=True)
        #create dynamic queries
        # query where category is not specified

        if len(guids)==0:
            return
        
        query = f"select id from {self.connection_details.table_prefix}_posts where guid IN %s"
        #query  = query  % ','.join("%s" * len(guids))

        query = query % str(tuple(guids))

        self.logger.info(query)

        

        try:
            cursor.execute(query)
            results = cursor.fetchall()
        except Exception:

            self.logger.error("An error occured with the query operation", exc_info=True)
            fetched_posts = 0
        # get the results as a python dictionary
        else:
            fetched_posts = cursor.rowcount

            self.logger.info(f"Updating {fetched_posts} posts category")
            window.update_gui(f"Updating {fetched_posts} posts category...")

            insert_query = f"INSERT INTO `{self.connection_details.table_prefix}_term_relationships` (`object_id`, `term_taxonomy_id`) VALUES (%s, %s)"
            
            posts_to_update = []

            for row in results:
                posts_to_update.append((row[0], 1))
 
            try:
                cursor.executemany(insert_query, posts_to_update)
                self.connection.commit()
                
            except Exception as e:
                self.logger.error("Error updating posts categories", exc_info=True)
            else:
                posts_updated = len(posts_to_update)
                self.logger.info("[%s] posts categories inserted in db", posts_updated)
                window.update_gui(f"[{posts_updated}] posts category have been updated")


    def close_conn(self):
        self.mysql_disconnect()
        self.close_ssh_tunnel()


    
        
            

        


    def mysql_disconnect(self):
        """Closes the MySQL database connection.
        """
        self.logger.info("Terminating remote connection")
        self.connection.close()
        self.close_ssh_tunnel()
        self.logger.info("Remote connection terminated")

    def close_ssh_tunnel(self):
        """Closes the SSH tunnel connection.
        """
        
        self.tunnel.close()

        



if __name__ == '__main__':

    db = Db()

    results = db.run_query()
    for row in results:
        print(row)



