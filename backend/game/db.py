from sqlmodel import SQLModel, create_engine
from ..config import get_settings
from .objects import *

_engine = create_engine(get_settings().sql_db_url)

def setup():
    SQLModel.metadata.create_all(_engine)

def get_engine():
    return _engine