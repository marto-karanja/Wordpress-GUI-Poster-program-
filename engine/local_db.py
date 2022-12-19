import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from sqlalchemy.sql.expression import func, select
from sqlalchemy import exc
from engine.models import BannedStrings, PublishedPosts, ProcessingPosts, ShortPosts, Process, TitleLength, ContentLength, WebsiteSettings, References

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


def get_content_length(db_session):
    content_length = db_session.query(ContentLength).get(1)
    if content_length is None:
        content_length = ContentLength(content_length=75)
        db_session.add(content_length)
        db_session.commit()
    return content_length.content_length

def set_content_length(db_session, length):
    content_length = db_session.query(ContentLength).get(1)
    content_length.content_length = length
    db_session.add(content_length)
    try:
        db_session.commit()
    except Exception as e:
        raise
    else:
        return


def save_website_records(engine, website_details):

    with create_threaded_session(engine) as session:
        website_record = WebsiteSettings(
            website_name = website_details['website_name'],
            ssh_host = website_details['ssh_host'],
            cpanel_username = website_details['cpanel_username'],
            ssh_password = website_details['ssh_password'],
            database_username = website_details['database_username'],
            database_password = website_details['database_password'],
            database_name = website_details['database_name'],
            table_prefix = website_details['database_prefix'],
            security_filepath = website_details["security_filepath"],        
        )
        
        session.add(website_record)
        try:
            session.commit()
        except Exception as e:
            raise
        else:
            print("Records saved successfully")
            return True


def get_website_records(engine):
    with create_threaded_session(engine) as session:
        records = session.query(WebsiteSettings).all()
        return {k.website_name : k.website_name for k in records}

def fetch_connection_details(engine, website):
    with create_threaded_session(engine) as session:
        records = session.query(WebsiteSettings).filter(WebsiteSettings.website_name == website).one()
        print(records)
        return records

def remove_website_records(engine, websites):
    with create_threaded_session(engine) as session:
        banned_string = delete(WebsiteSettings).where(WebsiteSettings.website_name.in_(websites))


        try:
            session.execute(banned_string)
            session.commit()
        except Exception as e:
            raise
        else:
            return True


    #----SQL Database Clean Up codes
TABLE_PARAMETER = "{TABLE_PARAMETER}"
DROP_TABLE_SQL = f"DROP TABLE '{TABLE_PARAMETER}';"
GET_TABLES_SQL = "SELECT name FROM sqlite_schema WHERE type='table';"


def delete_all_tables(con):
    tables = get_tables(con)
    delete_tables(con, tables)


def get_tables(con):
    cur = con.cursor()
    cur.execute(GET_TABLES_SQL)
    tables = cur.fetchall()
    cur.close()
    return tables


def delete_tables(con, tables):
    cur = con.cursor()
    for table, in tables:
        sql = DROP_TABLE_SQL.replace(TABLE_PARAMETER, table)
        cur.execute(sql)
    cur.close()



def save_references_to_db(engine, references):
    with create_threaded_session(engine) as db_session:
        if isinstance(references, list):
            references_list = []
            for l in references:            
                references_list.append(References(reference_name = l))
            db_session.add_all(references_list)
        else:
            db_session.add(References(reference_name = references))

        try:
            db_session.commit()
        except exc.IntegrityError as e:
            return False
        else:
            return True

def fetch_references(engine, limit):
    
    with create_threaded_session(engine) as db_session:
        references = db_session.query(References.reference_name).order_by(func.random()).limit(limit).all()

        for reference in references:
            print(reference)

        return references
