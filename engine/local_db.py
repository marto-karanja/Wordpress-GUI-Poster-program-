import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from engine.models import BannedStrings, PublishedPosts, ProcessingPosts, ShortPosts, Process, TitleLength

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


def save_short_posts(db_session, post_no, table):
    short = ShortPosts()
    short.link_no = post_no
    short.table_name = table
    db_session.add(short)
    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return

def fetch_short_posts(db_session, limit, offset= None):
    if offset != None:
        posts  = db_session.query(ShortPosts).limit(limit).offset(offset).all()
    else:
        posts  = db_session.query(ShortPosts).limit(limit).all()
    if len(posts) == 0:
        return False
    else:
        return [(k.link_no, k.table_name) for k in posts]

def fetch_published_posts(db_session, limit, offset= None):
    if offset != None:
        posts  = db_session.query(PublishedPosts).filter(PublishedPosts.status == Process.FALSE).limit(limit).offset(offset).all()
    else:
        posts  = db_session.query(PublishedPosts).filter(PublishedPosts.status == Process.FALSE).limit(limit).all()
    if len(posts) == 0:
        return False
    else:
        return [(k.link_no, k.website, k.table) for k in posts]

def count_published_posts(db_session):
    post_count = db_session.query(PublishedPosts).filter(PublishedPosts.status == Process.FALSE).count()
    return post_count


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

def delete_post(db_session, post_no):
    #post = db_session.query(PublishedPosts).filter_by(link_no = int(post_no)).delete()
    
    sql2 = delete(PublishedPosts).where(PublishedPosts.link_no == post_no)

    db_session.execute(sql2)

    
    try:
        db_session.commit()
    except Exception as e:
        raise
   
    return

def delete_multiple_posts(db_session, posts):
    #post = db_session.query(PublishedPosts).filter(PublishedPosts.id.in_(posts)).delete()
    deleted_posts = delete(PublishedPosts).where(PublishedPosts.link_no.in_(posts))
    

    try:
        db_session.execute(deleted_posts)
        db_session.commit()
    except Exception as e:
        print(e)
        return False
    else:
        return True

def delete_multiple_short_posts(db_session, posts):
    #post = db_session.query(PublishedPosts).filter(PublishedPosts.id.in_(posts)).delete()
    deleted_posts = delete(ShortPosts).where(ShortPosts.link_no.in_(posts))
    

    try:
        db_session.execute(deleted_posts)
        db_session.commit()
    except Exception as e:
        print(e)
        return False
    else:
        return True

        
def get_title_length(db_session):
    title_length = db_session.query(TitleLength).get(1)
    if title_length is None:
        title_length = TitleLength(title_length=25)
        db_session.add(title_length)
        db_session.commit()
    return title_length.title_length

def set_title_length(db_session, length):
    title_length = db_session.query(TitleLength).get(1)
    title_length.title_length = length
    db_session.add(title_length)
    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return