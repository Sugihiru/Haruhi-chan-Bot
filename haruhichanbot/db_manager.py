from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

Base = declarative_base()
# These globals are initialized in init_session()
engine = None
Session = None
session = None


def init_session(config):
    """
    Initialize the sqlalchemy session
    """
    global engine
    global Session
    global session

    connect_url = URL(
        config.sql_infos['db_api'],
        username=config.sql_infos['username'],
        password=config.sql_infos['password'],
        host=config.sql_infos['host'],
        port=config.sql_infos['port'],
        database=config.sql_infos['database'])

    engine = create_engine(connect_url, pool_recycle=3600)
    Session = sessionmaker(bind=engine)
    session = Session()
