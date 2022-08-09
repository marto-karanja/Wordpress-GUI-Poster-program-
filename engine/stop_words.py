from engine.local_db import connect_to_db, create_session, get_banned_strings


class BannedStrings(object):
    def __init__(self):
        """Initialize singleton class to fetch stop words"""
        # To Do
        # fetch database connection
        # fetch stop words
        self.stop_words = self.fetch_stop_words()

    
    def __new__(cls):
        """ creates a singleton object, if it is not created,
        or else returns the previous singleton object"""
        if not hasattr(cls, 'instance'):
            cls.instance = super(BannedStrings, cls).__new__(cls)
        return cls.instance

    def fetch_stop_words(self):
        """Fetch stop words from database"""
        engine = connect_to_db()
        if engine is False:
            return False
        else:
            session = create_session(engine)
            stop_words = get_banned_strings(session)
            session.close()
            print(stop_words)
            return stop_words

        

    