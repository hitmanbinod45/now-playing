from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    title = sa.Column(sa.String, index=True)
    artist = sa.Column(sa.String)
    spotify_id = sa.Column(sa.String)
    youtube_id = sa.Column(sa.String)
    apple_music_id = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, server_default=sa.func.now())