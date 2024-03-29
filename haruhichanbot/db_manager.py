from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

from . import exceptions

Base = declarative_base()
# These globals are initialized in init_session()
engine = None
Session = None
session = None


class UserAccounts(Base):
    __tablename__ = "user_accounts"
    account_id = Column(Integer, primary_key=True)
    # Note: most of the Discord snowflake ID are 18 characters
    # but there's no official infos on the max length of those ID
    discord_user_id = Column(String(20), nullable=False)
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


def insert_user_account(*, discord_user_id,
                        account_source,
                        account_server=None,
                        account_name,
                        comment=None):
    """
    Insert a new user account in database, and commit session
    If entry already exists, raise exceptions.DuplicateDbEntryWarning
    """
    exists = (session.query(UserAccounts.account_id)
                     .filter_by(discord_user_id=discord_user_id,
                                account_source=account_source,
                                account_server=account_server,
                                account_name=account_name)
                     .scalar() is not None)
    if exists:
        raise exceptions.DuplicateDbEntryWarning(
            "Duplicate entry in database. Value not inserted.")

    dbobj = UserAccounts(discord_user_id=discord_user_id,
                         account_source=account_source,
                         account_server=account_server,
                         account_name=account_name,
                         comment=comment)
    session.add(dbobj)
    session.commit()


def get_accounts_for_user(discord_user_id):
    """Get all accounts linked to Discord user
    Sorted by source, server (if applicable) and name"""
    return (session.query(UserAccounts.account_source,
                          UserAccounts.account_server,
                          UserAccounts.account_name)
                   .filter_by(discord_user_id=discord_user_id)
                   .order_by(UserAccounts.account_source,
                             UserAccounts.account_server,
                             UserAccounts.account_name)
                   .all())


def get_accounts_for_source_and_server(*, account_source, account_server=None):
    query = session.query(UserAccounts.discord_user_id,
                          UserAccounts.account_server,
                          UserAccounts.account_name)

    if account_server:
        query = query.filter_by(account_source=account_source,
                                account_server=account_server)
    else:
        query = query.filter_by(account_source=account_source)

    return query.order_by(UserAccounts.account_server,
                          UserAccounts.account_name).all()


def remove_server_accounts_for_user(*, discord_user_id,
                                    account_source, account_server=None):
    """Remove all accounts linked to discord user
    on specified account_source and account_server"""
    query = session.query(UserAccounts.account_id)

    if account_server:
        query = query.filter_by(account_source=account_source,
                                account_server=account_server)
    else:
        query = query.filter_by(account_source=account_source)

    nb_removed = query.delete()
    session.commit()
    return nb_removed


def remove_account(*, discord_user_id,
                   account_source,
                   account_server=None,
                   account_name):
    """Remove a specific account"""
    query = session.query(UserAccounts.account_id)

    query = query.filter_by(account_source=account_source,
                            account_name=account_name)
    if account_server:
        query = query.filter_by(account_server=account_server)

    nb_removed = query.delete()
    session.commit()
    return nb_removed
