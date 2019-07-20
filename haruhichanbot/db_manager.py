from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

Base = declarative_base()
# These globals are initialized in init_session()
engine = None
Session = None
session = None


class UserAccounts(Base):
    __tablename__ = "user_accounts"
    account_id = Column(Integer, primary_key=True)
    discord_user_id = Column(Integer, nullable=False)
    account_source = Column(String(64), nullable=False)
    account_server = Column(String(64))
    account_name = Column(String(64), nullable=False)
    comment = Column(Text)


def init_session(config):
    """
    Initialize the sqlalchemy session and create tables in database
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
    Base.metadata.create_all(engine)
