import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from engine.models import BannedStrings, PublishedPosts, ProcessingPosts, ShortPosts, Process

def get_connection(database_url):
    return create_engine(database_url, echo=False, connect_args={'check_same_thread': False})

def connect_to_db():
    database_url = "{}\{}".format(os.getcwd(), "settings.db")
    try:        
        # GET THE CONNECTION OBJECT (ENGINE) FOR THE DATABASE
        engine = get_connection(f"sqlite:///{database_url}")
    except Exception as ex:
        print("Connection could not be made due to the following error: \n", ex)
        return False
    else:
        print("Connection created successfully.")
        return engine


def get_banned_strings(db_session):
    strings  = db_session.query(BannedStrings).all()
    return {k.string_value : k.string_id for k in strings}



def add_banned_string(db_session, banned_strings):
    if isinstance(banned_strings, list):
        banned_list = []
        for l in banned_strings:            
            banned_list.append(BannedStrings(string_value = l))
        db_session.add_all(banned_list)
    else:
        db_session.add(BannedStrings(string_value = banned_strings))

    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return True


#---------------------------------------------------
def delete_banned_string(db_session, string_ids):
    from sqlalchemy import delete
    banned_string = delete(BannedStrings).where(BannedStrings.string_id.in_(string_ids))


    try:
        db_session.execute(banned_string)
        db_session.commit()
    except Exception as e:
        raise
    else:
        return True

def create_session(engine):
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session()


def create_threaded_session(engine):
    session_factory = sessionmaker(bind=engine)
    global Session
    Session = scoped_session(session_factory)
    session = Session()
    return session


def remove_session():
    global Session
    Session.remove()

def save_published_posts(db_session, post):
    db_session.add(post)
    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return


def save_short_posts(db_session, post_no):
    short = ShortPosts()
    short.link_no = post_no
    db_session.add(short)
    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return

def fetch_published_posts(db_session, limit, offset):
    posts  = db_session.query(PublishedPosts).filter(PublishedPosts.status == Process.FALSE).limit(limit).offset(offset).all()
    if len(posts) == 0:
        return False
    else:
        return [(k.link_no, k.website, k.table) for k in posts]


def update_post(db_session, post_no):
    post = db_session.query(PublishedPosts).filter_by(link_no = int(post_no)).first()
    post.status = Process.TRUE

    db_session.add(post)
    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return