import logging
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost


class WpPost():
    """class that posts to wordpress"""
    def __init__(self, url, user, password, logger = None):
        """initialize class"""
        self.url = url
        self.password = password
        self.user = user
        self.site = Client(url, user, password)
        self.logger = logger or logging.getLogger(__name__)

    def publish_post(self, title, content, categories):
        """publishes post"""
        post = WordPressPost()
        post.title = title
        post.content = content
        post.terms_names = {
            'category': categories
        }
        post.post_status = 'publish'
        try:
            # modifying post function to report success or failure
            self.site.call(NewPost(post))
            self.logger.debug("%s published to %s", title, self.url)
            return True
        except Exception:
            # log exception
            self.logger.error('Failed to publish post to : %s',self.url, exc_info=True)
            return False;

        
        