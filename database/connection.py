from sqlmodel import SQLModel, Session, create_engine
from models.user import User
import config

engine_url = create_engine(
    config.DATABASE_URL,
    connect_args={'check_same_thread': False}
)

def conn():
    SQLModel.metadata.create_all(engine_url)

def get_session():
    with Session(engine_url) as session:
        yield session
