from re import L
import requests
import json
import time
import base64
import logging

from datetime import datetime

class RestPost():
    def __init__(self, url, user, password, logger = None):
        """initialize class"""
        self.logger = logger or logging.getLogger(__name__)
        self.url = url
        self.password = password
        self.user = user
        self.build_authentication(user, password)

    def build_authentication(self, user, password):

        credentials = user + ':' + password
        token = base64.b64encode(credentials.encode())
        self.header = {
            'Authorization': 'Basic ' + token.decode('utf-8'), 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36'
            }
        

    def get_current_time(self):
        d = datetime.now()
        d = d.strftime("%Y-%m-%dT%H:%M:%S")
        return d


    def publish_post(self, title, content, categories):


        url = "{}/wp-json/wp/v2/posts".format(self.url)
        # get category id
        """
        categories_id = self.check_category_exits(categories)
        categories_id = [str(i) for i in categories_id]


        category = ''
        if len(categories_id) > 0: 
            category = ','.join(categories_id)"""
            

        post = {
        'title'    : title,
        'status'   : 'publish', 
        'content'  : content,
        'categories': "",
        'date'   : self.get_current_time()
        }
        response = requests.post(url , headers=self.header, json=post)
        self.logger.debug("Connecting to %s: Code: %s",self.url, response.status_code)
        if response.status_code >= 200 and response.status_code < 300:
            return True
        else:
            self.logger.error("Unable to publish post. Error Code: [%s]", response.status_code)
            self.logger.error("Server reason: [%s]", response.reason)
            return False

    def check_category_exits(self, categories):
        

        category_url = "{}/wp-json/wp/v2/categories".format(self.url)

        categories_id = []

        for category in categories:
            arguments = {
                "search" : category
                }

            response = requests.get(category_url, headers=self.header, json = arguments)
            self.logger.debug("Connecting to %s: Response Code: [%s]",self.url, response.status_code)
            time.sleep(2)

            # if category does not exist create new category
            if len(response.json()) == 0:
                categories_id.append(self.create_category(category))
                time.sleep(2)
            else:
                for item in response.json():
                    categories_id.append(item["id"])
        return categories_id

    def create_category(self, category): 
        create_category_url = "{}/wp-json/wp/v2/categories".format(self.url)
        
        header = self.header

        arguments = {
            "name" : category
            }

        response = requests.post(create_category_url , headers=header, json = arguments)
        self.logger.debug("Connecting to %s: Code: %s",self.url, response.status_code)
        if response.status_code >= 200 and response.status_code < 300:
            return response.json()['id']
        else:
            return False