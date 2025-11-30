from sqlalchemy import create_engine, Column, Integer, String, Float, select, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import or_

from jarvis_botz.config import config

import dotenv
dotenv.load_dotenv()
import os


POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

if config.stage == 'dev':
    POSTGRES_HOST = os.getenv("DEV_HOST")
else:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")

url = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_async_engine(
    url,
    echo=False
    )


SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autoflush=True)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'


    id = Column(BigInteger, primary_key=True)
    username = Column(String, unique=True)
    tokens = Column(Float, default=10)
    role = Column(String, default='user')


    




async def _get_user(session, id=None, username=None):
    stmt = select(User).filter(or_(User.id == id, User.username == username))
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise ValueError('User don`t found')
    return user




async def get_user(id=None, username=None):
    async with SessionLocal() as session:
        user = await _get_user(session=session, id=id, username=username)
        return user
    

async def add_user(id, username):
    async with SessionLocal() as session:
        user = User(id=id, username=username)
        session.add(user)
        await session.commit()
        return user
    

async def _set_attr(id=None, username=None, column:str=None, value=None):
    async with SessionLocal() as session:
        user = await _get_user(session=session, id=id, username=username)
        setattr(user, column, value)
        await session.commit()
        return True
    
    