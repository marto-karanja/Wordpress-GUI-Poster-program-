import logging
from xmlrpc.client import ProtocolError
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
from wordpress_xmlrpc.exceptions import ServerConnectionError


class WpPost():
    """class that posts to wordpress"""
    def __init__(self, url, user, password, logger = None):
        """initialize class"""
        self.logger = logger or logging.getLogger(__name__)
        self.url = url
        self.password = password
        self.user = user

        try:
            self.logger.info('Connecting to: [%s]',self.url)
            self.site = Client(url, user, password)
            self.logger.info('Connection successful')
        except Exception:
            self.logger.error('Failed to connect to : %s',self.url, exc_info=True)
        

    def publish_post(self, title, content, categories):
        """publishes post"""
        post = WordPressPost()
        post.title = title
        post.content = content
        post.terms_names = {
            'category': categories
        }
        post.post_status = 'publish'
        if hasattr(self,'site'):

            try:
                # modifying post function to report success or failure
                self.site.call(NewPost(post))
                self.logger.debug("%s published to %s", title, self.url)
                return True
            except ProtocolError:
                self.logger.error('Incorrect Username or pasword  : %s',self.url)
                self.logger.error('Failed to publish post to : %s',self.url, exc_info=True)
                return False

            except Exception:
                # log exception
                self.logger.error('Failed to publish post to : %s',self.url, exc_info=True)
                return False
        else:
            self.logger.error('Unable to publish post. Website not connected')
            return False

        
        