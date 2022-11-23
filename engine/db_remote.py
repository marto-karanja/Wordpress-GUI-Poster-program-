# Db Access Class
from mysql.connector.locales.eng import client_error
import mysql.connector
import logging
import socket
import paramiko
import os
import sshtunnel
from sshtunnel import SSHTunnelForwarder


class Db(object):
    """Db access class"""

    def __init__(self, logger = None, connection = None):
        self.logger = logger or logging.getLogger(__name__)
        self.open_ssh_tunnel(verbose=True)
        self.mysql_connect()

    def mysql_connect(self):
        """Connect to a MySQL server using the SSH tunnel connection
        
        :return connection: Global MySQL database connection
        """

        database_username = 'buyapcan_wp337'
        database_password = '!D=sv)~tAG7KVT<2'
        database_name = 'buyapcan_wp337'
        
        
        self.connection = mysql.connector.connect(
            host='127.0.0.1',
            user=database_username,
            passwd=database_password,
            db=database_name,
            port=self.tunnel.local_bind_port,
            use_pure=True,
            charset='utf8',
            use_unicode=True
        )


    def open_ssh_tunnel(self, verbose=False):
        """Open an SSH tunnel and connect using a username and password.
        
        :param verbose: Set to True to show logging
        :return tunnel: Global SSH tunnel connection

         """
        ssh_host = '198.54.116.72'
        ssh_username = 'buyapcan'
        ssh_password = 'incorrect0727531915'

        localhost = '127.0.0.1'

        
        if verbose:
            sshtunnel.DEFAULT_LOGLEVEL = logging.DEBUG


        k = paramiko.RSAKey.from_private_key_file((os.getcwd() +"\\key\\buyapcan_key"),ssh_password) 
        
        
        self.tunnel = SSHTunnelForwarder(
            (ssh_host, 21098),
            ssh_private_key=k,
            ssh_username = ssh_username,
            remote_bind_address = ('127.0.0.1', 3306)
        )
        
        self.tunnel.start()

    def run_query(self):
        """method to fetch posts"""
        #create cursor object
        cursor = self.connection.cursor(dictionary=True)
        #create dynamic queries
        # query where category is not specified
        query  = "select * from wplr_posts limit  100"

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
        return results

def mysql_disconnect(self):
    """Closes the MySQL database connection.
    """
    
    self.connection.close()

def close_ssh_tunnel(self):
    """Closes the SSH tunnel connection.
    """
    
    self.tunnel.close

        



if __name__ == '__main__':

    db = Db()

    results = db.run_query()
    for row in results:
        print(row)



