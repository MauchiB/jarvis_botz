from sqlalchemy import select, update, Boolean, Integer, String, DateTime, Numeric
from sqlalchemy import or_
from sqlalchemy.orm import selectinload, joinedload


import os
import json
import redis

from jarvis_botz.bot.db.schemas import User, Sub
from jarvis_botz.config import Config

ALLOWED_COLUMNS_UPDATE = ['tokens']


from telegram.ext import BasePersistence, PersistenceInput

from typing import Dict, Optional, Tuple, Any, List

from jarvis_botz import app

class UserRepository:
    def __init__(self, session):
        self.session = session
    


    async def get_user(self, id=None, username=None) -> User:
        stmt = select(User).filter(or_(User.id == id, User.username == username)).options(selectinload(User.subscribers), 
                                                                                          selectinload(User.referrals), 
                                                                                          joinedload(User.referral))
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        return user
    

        

    async def add_user(self, id, username, chat_id) -> User:
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

        

    async def get_users_by_role(self, role) -> List[User]:
        query = select(User).filter_by(role=role)
        result = await self.session.execute(query)
        result = result.scalars().all()
        return result
    

    async def update_ref_user(self, user_id, ref_user_id) -> None:
        current_user = await self.get_user(id=user_id)
        ref_user = await self.get_user(id=ref_user_id)

        if current_user and ref_user:
            if current_user == ref_user:
                return
            if current_user.referral_id is not None:
                return
            
            current_user.referrer = ref_user
            await self.session.commit()
    


    


    


from typing import Any, Dict, Optional, Tuple

class RedisPersistence(BasePersistence):
    def __init__(
        self, 
        redis_client: redis.asyncio.StrictRedis,
        cfg: Config,
        store_data: Optional[PersistenceInput] = None,
        update_interval: float = 60
    ):
        super().__init__(store_data=store_data, update_interval=update_interval)
        self.redis_client = redis_client
        self.cfg = cfg

    @classmethod
    async def create(cls, cfg: Config, store_data: Optional[PersistenceInput] = None, update_interval: float = 60):
        client = redis.asyncio.StrictRedis(
            host=cfg.redis_host,
            port=cfg.redis_port,
            decode_responses=True
        )
        await client.ping()
        return cls(redis_client=client, cfg=cfg, store_data=store_data, update_interval=update_interval)


    async def get_bot_data(self) -> Dict[str, Any]:
        data = await self.redis_client.hget(self.cfg.redis_bot_prefix, "global")
        return json.loads(data) if data else {}


    async def update_bot_data(self, data: Dict[str, Any]) -> None:
        await self.redis_client.hset(self.cfg.redis_bot_prefix, "global", json.dumps(data))


    async def get_user_data(self) -> Dict[int, Dict[Any, Any]]:
        raw_data = await self.redis_client.hgetall(self.cfg.redis_user_prefix)
        if not raw_data:
            return {}

        return {int(k): json.loads(v) for k, v in raw_data.items()}

    async def update_user_data(self, user_id: int, data: Dict[Any, Any]) -> None:
        await self.redis_client.hset(self.cfg.redis_user_prefix, str(user_id), json.dumps(data))

    
    async def refresh_user_data(self, user_id: int, user_data: Any, push:bool=True) -> None:
        print('refreshing user data...')
        if push:
            # Вариант "Я изменил данные в Боте, сохрани их в Редис"
            await self.update_user_data(user_id, user_data)
        else:
            raw = await self.redis_client.hget(self.cfg.redis_user_prefix, str(user_id))
            if raw:
                user_data.update(json.loads(raw))




    async def get_conversations(self, name: str) -> Dict[Tuple[Any, ...], Any]:
        raw_data = await self.redis_client.hgetall(f"{self.cfg.redis_conv_prefix}:{name}")
        if not raw_data:
            return {}
        
        conversations = {}
        for k, v in raw_data.items():
            try:
                parts = k.split('_')
                key = tuple(int(p) for p in parts)
                conversations[key] = json.loads(v)
            except:
                continue
        return conversations

    async def update_conversation(self, name: str, key: Tuple[int, ...], new_state: Optional[Any]) -> None:
        str_key = "_".join(str(p) for p in key)
        if new_state is None:
            await self.redis_client.hdel(f"{self.cfg.redis_conv_prefix}:{name}", str_key)
        else:
            await self.redis_client.hset(f"{self.cfg.redis_conv_prefix}:{name}", str_key, json.dumps(new_state))


    async def get_chat_data(self) -> Dict[int, Dict[Any, Any]]:
        raw_data = await self.redis_client.hgetall(self.cfg.redis_chat_prefix)
        return {int(k): json.loads(v) for k, v in raw_data.items()} if raw_data else {}

    async def update_chat_data(self, chat_id: int, data: Dict[Any, Any]) -> None:
        await self.redis_client.hset(self.cfg.redis_chat_prefix, str(chat_id), json.dumps(data))

    async def flush(self) -> None:
        await self.redis_client.aclose()

    async def drop_chat_data(self, chat_id: int) -> None: 
        await self.redis_client.hdel(self.cfg.redis_chat_prefix, str(chat_id))

    async def drop_user_data(self, user_id: int) -> None:
        await self.redis_client.hdel(self.cfg.redis_user_prefix, str(user_id))



    async def refresh_bot_data(self, bot_data: Dict) -> None: pass
    async def refresh_chat_data(self, chat_id: int, chat_data: Any) -> None: pass
    async def get_callback_data(self) -> None: pass
    async def update_callback_data(self, data) -> None: pass




    async def get_all_chats(self, user_id):
        chats = await self.redis_client.hgetall(f"{self.cfg.redis_metadata_prefix}:{user_id}")
        return {k: json.loads(v) for k, v in chats.items()} if chats else {}

    async def delete_chat_metadata(self, user_id, session_id):
        await self.redis_client.hdel(f"{self.cfg.redis_metadata_prefix}:{user_id}", session_id)
        
    async def update_chat_metadata(self, user_id, session_key, metadata: dict):
        existing_data = await self.get_chat_metadata(user_id, session_key)
        
        if existing_data:
            existing_data.update(metadata)
            final_data = existing_data

        else:
            final_data = metadata

        await self.redis_client.hset(
            f"{self.cfg.redis_metadata_prefix}:{user_id}", 
            session_key, 
            json.dumps(final_data)
        )

    async def get_chat_metadata(self, user_id, session_key):
        data = await self.redis_client.hget(f"{self.cfg.redis_metadata_prefix}:{user_id}", session_key)
        return json.loads(data) if data else None
    


    async def close(self):
        await self.redis_client.close()

