from sqlalchemy import select, update, Boolean, Integer, String, DateTime, Numeric
from sqlalchemy import or_
from sqlalchemy.orm import selectinload


import os
import json
import redis

from jarvis_botz.bot.db.schemas import User, Sub
from jarvis_botz.config import Config

ALLOWED_COLUMNS_UPDATE = ['tokens']


from telegram.ext import BasePersistence, PersistenceInput

from typing import Dict, Optional, Tuple, Any


class UserRepository:
    def __init__(self, session):
        self.session = session
    


    async def get_user(self, id=None, username=None):
        stmt = select(User).filter(or_(User.id == id, User.username == username)).options(selectinload(User.subsribers))
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        return user
    

        

    async def add_user(self, id, username, chat_id):
        user = User(id=id, username=username, chat_id=chat_id)
        self.session.add(user)
        await self.session.commit()
        return user
        

    async def _set_attr(self, id=None, username=None, update_data:dict=None):
        stmt = (
            update(User)
            .where((or_(User.id == id, User.username == username)))
            .values(**update_data)
        )

        await self.session.execute(stmt)
        await self.session.commit()

        

    async def get_users_by_role(self, role):
        query = select(User).filter_by(role=role)
        result = await self.session.execute(query)
        result = result.scalars().all()
        return result
    


    


    

class RedisPersistence(BasePersistence):
    _instance = None
    
    def __init__(self, 
                 redis_client: redis.asyncio.StrictRedis,
                 cfg: Config,
                 store_data: Optional[PersistenceInput] = None, # Добавляем это
                 update_interval: float = 60):
        super().__init__(store_data=store_data, update_interval=update_interval)
        self.redis_client = redis_client
        self.cfg = cfg


    @classmethod
    async def create(cls, cfg: Config, store_data: Optional[PersistenceInput] = None, update_interval: float = 60):
        client = await cls._get_client(cfg)
        return cls(redis_client=client, cfg=cfg, store_data=store_data, update_interval=update_interval)


    @classmethod
    async def _get_client(cls, cfg: Config):
        print(f'Connecting to Redis at {cfg.redis_url}...')
        client = await redis.asyncio.StrictRedis(
            host=cfg.redis_host,
            decode_responses=True
        )
        ping = await client.ping()
        print(f'Connection ping is {ping}')
        return client
    



    async def _get_all_data(self, prefix):
        keys = await self.redis_client.keys(f'{prefix}:*')
        all_user_data = {}
        for key in keys:
            user_id = int(key.split(':')[1])
            raw_data = await self.redis_client.get(key)
            all_user_data[user_id] = json.loads(raw_data)

        return all_user_data
    


    async def _update_data(self, name, key, value):
        await self.redis_client.hset(name=name, key=key, value=value)
    

    async def get_bot_data(self):
        return await self._get_all_data(self.cfg.redis_bot_prefix)
    

    async def get_user_data(self):
        return await self._get_all_data(self.cfg.redis_user_prefix)
    

    async def get_conversations(self, name):
        return await self._get_all_data(f'{self.cfg.redis_chat_prefix}:{name}')
    

    async def update_bot_data(self, data):
        return await self._update_data(name=self.cfg.redis_bot_prefix, key='global', value=json.dumps(data))
    

    async def update_user_data(self, user_id, data):
        return await self._update_data(name=self.cfg.redis_user_prefix, key=user_id, value=json.dumps(data))
    
    async def update_conversation(self, name, key, new_state):
        return await self._update_data(name=name, key=f'{key[0]}_{key[1]}', value=new_state)
    

    async def flush(self) -> None:
        if self.redis_client:
            await self.redis_client.aclose()
    


    async def get_chat_data(self) -> Dict[int, Any]: return {}
    async def update_chat_data(self, chat_id: int, data: Dict) -> None: pass
    async def drop_chat_data(self, chat_id: int) -> None: pass
    async def drop_user_data(self, user_id: int) -> None: pass
    async def refresh_bot_data(self, bot_data: Dict) -> None: pass
    async def refresh_chat_data(self, chat_id: int, chat_data: Any) -> None: pass
    async def refresh_user_data(self, user_id: int, user_data: Any) -> None: pass
    async def get_callback_data(self) -> Optional[Tuple[Any, Any]]: return None
    async def update_callback_data(self, data: Tuple[Any, Any]) -> None: pass
    


    

    async def delete_chat(self, user_id: str, session_id: str):
        await self.redis_client.delete(f'{self.cfg.redis_history_prefix}:{session_id}')
        await self.redis_client.hdel(f'{self.cfg.redis_chat_prefix}:{user_id}', session_id)


    async def create_chat(self, user_id, session_key, metadata: dict):
        await self._update_data(f'{self.cfg.redis_chat_prefix}:{user_id}', key=session_key, value=json.dumps(metadata))


    async def get_chat(self, user_id, session_key):
        chat = await self.redis_client.hget(f'{self.cfg.redis_chat_prefix}:{user_id}', session_key)
        if chat:
            chat = json.loads(chat)
        return chat


    async def get_all_chats(self, user_id):
        chats = await self.redis_client.hgetall(f'{self.cfg.redis_chat_prefix}:{user_id}')
        all_chats = {}
        for k, chat in chats.items():
            all_chats[k] = json.loads(chat)
        return all_chats
    
    
    