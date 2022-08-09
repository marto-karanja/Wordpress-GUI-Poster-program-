from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BannedStrings(Base):
   __tablename__ = 'Banned Strings'
   string_id = Column(Integer, primary_key=True)
   string_value = Column(String)


class PublishedPosts(Base):
    __tablename__ = 'Published Posts'
    id = Column(Integer, primary_key=True)
   
class ProcessingPosts(Base):
    __tablename__ = 'Processing Posts'
    id = Column(Integer, primary_key=True)
