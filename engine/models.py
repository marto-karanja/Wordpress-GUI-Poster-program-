import enum

from xmlrpc.client import Boolean
from sqlalchemy import Column, Integer, String, ForeignKey, Table, Enum, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BannedStrings(Base):
   __tablename__ = 'Banned Strings'
   string_id = Column(Integer, primary_key=True)
   string_value = Column(String)

class Process(enum.Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"


class PublishedPosts(Base):
    __tablename__ = 'Published Posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    link_no = Column(Integer)
    website = Column(String)
    table = Column(String)
    status = Column(Enum(Process), server_default=Process.FALSE.value)

class ShortPosts(Base):
    __tablename__ = 'Short Posts'
    id = Column(Integer, primary_key=True)
    link_no = Column(Integer)
    status = Column(Enum(Process), server_default=Process.FALSE.value)
    table_name = Column(String)

   
class ProcessingPosts(Base):
    __tablename__ = 'Processing Posts'
    id = Column(Integer, primary_key=True)

class TitleLength(Base):
    __tablename__ = 'Title Length'
    id = Column(Integer, primary_key=True)
    title_length = Column(String, server_default='25')
    
