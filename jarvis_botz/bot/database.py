from sqlalchemy import create_engine, Column, Integer, String, Float, select, BigInteger, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import or_

from jarvis_botz.config import config

import dotenv
dotenv.load_dotenv()
import os
import json

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
    is_banned = Column(Boolean, default=False)
    created_at = Column(String)
    last_active_at = Column(String)
    chat_id = Column(String, default='')

    subsribers = relationship("Sub", back_populates="user")


class Sub(Base):
    __tablename__ = 'subscribers'


    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    subscription_start_date = Column(String)
    subscription_end_date = Column(String)
    tokens_purchased = Column(Float, default=0)

    user = relationship("User", back_populates="subsribers")


    


async def _get_user(session, id=None, username=None):
    stmt = select(User).filter(or_(User.id == id, User.username == username))
    result = await session.execute(stmt)
    user = result.scalars().first()
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
        return user
    




import redis

async def get_redis_client():
    client = await redis.asyncio.StrictRedis(
        host=os.getenv("REDIS_URL", "localhost"),
        decode_responses=True
    )
    return client


async def delete_chat_redis(prefix_history, prefix_metadata, user_id: str, session_id: str):
    client = await get_redis_client()
    await client.delete(f'{prefix_history}:{session_id}')
    await client.hdel(f'{prefix_metadata}:{user_id}', session_id)
    return True



async def create_chat_redis(prefix_metadata, name, key, metadata: dict):
    client = await get_redis_client()
    metadata = json.dumps(metadata)
    await client.hset(f'{prefix_metadata}:{name}', key=key, value=metadata)
    return True


async def get_chat_redis(prefix_metadata, name, key):
    client = await get_redis_client()
    chat = await client.hget(f'{prefix_metadata}:{name}', key)
    if chat:
        chat = json.loads(chat)
    else: chat = None
    return chat


async def get_all_chats_redis(prefix_metadata, name):
    client = await get_redis_client()
    chats = await client.hgetall(f'{prefix_metadata}:{name}')
    all_chats = {}
    for k, chat in chats.items():
        all_chats[k] = json.loads(chat)
    return all_chats
    
    
    