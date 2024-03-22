import os
# from settings.config import database_url


class BaseConfig:
    DEBUG = True
    # Configure SQLAlchemy for storing the session data on the server-side
    SESSION_TYPE = 'sqlalchemy'
    SESSION_PERMANENT = True
    
    SQLALCHEMY_POOL_SIZE=10
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   
 
class TestConfig(BaseConfig):
    TESTING = True
     #SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'    
     # SQLALCHEMY_TRACK_MODIFICATIONS = False    
     # SESSION_TYPE = 'sqlalchemy'    
     # # SESSION_PERMANENT = True    
     # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:India123@db:5432/nam_backend'    
     # PERMANENT_SESSION_LIFETIME = 1


class ProdConfig(BaseConfig):
    DEBUG = False



