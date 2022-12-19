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



class Db(object):
    """Db access class"""

    def __init__(self, logger = None, connection_details = None):

        self.connection_details = connection_details

        self.logger = logger or logging.getLogger(__name__)

        self.connection_attempts = 1
        
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

        self.tunnel = sshtunnel.SSHTunnelForwarder(
                (self.connection_details.ssh_host, 21098),
                ssh_private_key=security_key,
                ssh_username = self.connection_details.cpanel_username,
                set_keepalive = 12000,
                remote_bind_address = ('127.0.0.1', 3306)
            )
            
        self.tunnel.start()
        

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

    

    def bulk_insert_posts(self, records_to_update, window):
        # get publishing date
        if (self.tunnel.is_active):
                cursor = self.connection.cursor()
                query = f"INSERT INTO {self.connection_details.table_prefix}_posts (`post_title`, `post_name`, `post_content`, `post_excerpt`, `post_status`, `comment_status`, `post_date`, `post_date_gmt`, `post_modified`,`post_modified_gmt`,`guid`, `post_author`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, %s,%s,%s)"
                
                try:
                    cursor.executemany(query, records_to_update)
                    self.connection.commit()
                    x = len(records_to_update)
                                        
                except ConnectionAbortedError as e:
                    self.logger.info("A connection error has occured")
                    window.update_gui("A connection error has occured")
                    if self.connection_attempts <= 3:
                        self.logger.info(f"Connection attempt: {self.connection_attempts}")

                        self.connection_attempts = self.connection_attempts + 1

                        self.open_ssh_tunnel()
                        self.connect_to_mysql()
                        self.bulk_insert_posts(records_to_update)
                    else:
                        self.logger.info("Unable to connect to db after multiple attempts")
                        window.update_gui("Unable to connect to db after multiple attempts")

                except:
                    self.connection.rollback()
                    self.logger.warning("[%s] posts failed to insert in db", len(records_to_update))
                    self.logger.error('Problem with update operation', exc_info=True)
                    window.update_gui("Problem publishing posts to database")
                    cursor.close()
                    return False
                else:
                    self.logger.info("[%s] posts inserted in db", x)
                    window.update_gui(f"[{x}] posts inserted in database")
                    # update post category
                    guids = [record[-2] for record in records_to_update]
                    self.update_post_category(guids, cursor = cursor, window= window)
                    self
                    return True
                finally:
                    cursor.close()
        else:
            self.logger.info(f"A connection error has occured")
            if self.connection_attempts <= 3:
                self.logger.info(f"Connection attempt: {self.connection_attempts}")

                self.connection_attempts = self.connection_attempts + 1

                self.close_ssh_tunnel()
                self.open_ssh_tunnel()
                self.connect_to_mysql()
                self.bulk_insert_posts(records_to_update)
            else:
                self.logger.info(f"Unable to connect to db after multiple attempts")


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



