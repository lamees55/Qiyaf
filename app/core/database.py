from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

def init_db():
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        session.commit()
    
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session