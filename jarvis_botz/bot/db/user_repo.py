from sqlalchemy import or_, select, update
from sqlalchemy.orm import selectinload, joinedload
import json
from telegram.ext import BasePersistence, PersistenceInput
from typing import Dict, Optional, Tuple, Any, List
from jarvis_botz.bot.db.schemas import User
from jarvis_botz.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
ALLOWED_COLUMNS_UPDATE = ['tokens']




class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session




    async def get_user(
        self,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        with_refs: bool = True,
    ) -> Optional[User]:

        if user_id is None and username is None:
            raise ValueError("user_id or username must be provided")

        conditions = []
        if user_id is not None:
            conditions.append(User.id == user_id)
        if username is not None:
            conditions.append(User.username == username)

        stmt = select(User).where(or_(*conditions))

        if with_refs:
            stmt = stmt.options(
                selectinload(User.referrals),
                joinedload(User.referral),
            )

        result = await self.session.execute(stmt)
        return result.scalars().first()




    async def add_user(self, *, user_id: int, username: str, chat_id: int) -> User:
        user = User(id=user_id, username=username, chat_id=chat_id)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        await self.session.commit()

        return user



    async def update_user_fields(
        self,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        update_data: dict,
    ) -> None:

        if not update_data:
            return

        if user_id is None and username is None:
            raise ValueError("user_id or username must be provided")

        conditions = []
        if user_id is not None:
            conditions.append(User.id == user_id)
        if username is not None:
            conditions.append(User.username == username)

        stmt = (
            update(User)
            .where(or_(*conditions))
            .values(**update_data)
        )

        await self.session.execute(stmt)
        await self.session.commit()



    async def get_users_by_role(self, role: str) -> List[User]:
        stmt = select(User).where(User.role == role)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())



    async def update_ref_user(self, user_id: int, ref_user_id: int) -> None:
        if user_id == ref_user_id:
            return


        current_user = await self.get_user(user_id=user_id, with_refs=False)
        ref_user = await self.get_user(user_id=ref_user_id, with_refs=False)

        if not current_user or not ref_user:
            return

        if current_user.referral_id is not None:
            return

        if ref_user.referral_id == current_user.id:
            return

        current_user.referral = ref_user
        await self.session.commit()

    




class RedisPersistence(BasePersistence):
    def __init__(
        self,
        redis_client: redis.Redis,
        cfg: Config,
        store_data: Optional[PersistenceInput] = None,
        update_interval: float = 60,
    ) -> None:
        super().__init__(store_data=store_data, update_interval=update_interval)
        self.redis: redis.Redis = redis_client
        self.cfg: Config = cfg



    @classmethod
    async def create(
        cls,
        cfg: Config,
        store_data: Optional[PersistenceInput] = None,
        update_interval: float = 60,
    ) -> "RedisPersistence":
        client = redis.Redis(
            host=cfg.redis.host,
            port=cfg.redis.port,
            decode_responses=True,
        )
        await client.ping()
        return cls(client, cfg, store_data, update_interval)

 

    def _dump(self, data: Any) -> str:
        return json.dumps(data)

    def _load(self, data: Optional[str]) -> Any:
        return json.loads(data) if data else None



    def _bot_key(self) -> str:
        return self.cfg.redis.bot_prefix

    def _user_key(self) -> str:
        return self.cfg.redis.user_prefix

    def _chat_key(self) -> str:
        return self.cfg.redis.chat_prefix

    def _conv_key(self, name: str) -> str:
        return f"{self.cfg.redis.conv_prefix}:{name}"

    def _meta_key(self, user_id: int, session_id: str) -> str:
        return f"{self.cfg.redis.metadata_prefix}:{user_id}:{session_id}"

    def _session_set_key(self, user_id: int) -> str:
        return f"{self.cfg.redis.chat_sessions_prefix}:{user_id}"

 

    async def get_bot_data(self) -> Dict[str, Any]:
        raw = await self.redis.hget(self._bot_key(), "global")
        return self._load(raw) or {}

    async def update_bot_data(self, data: Dict[str, Any]) -> None:
        await self.redis.hset(self._bot_key(), "global", self._dump(data))



    async def get_user_data(self) -> Dict[int, Dict[Any, Any]]:
        raw = await self.redis.hgetall(self._user_key())
        return {int(k): self._load(v) for k, v in raw.items()} if raw else {}

    async def update_user_data(self, user_id: int, data: Dict[Any, Any]) -> None:
        await self.redis.hset(self._user_key(), str(user_id), self._dump(data))

    async def refresh_user_data(
        self,
        user_id: int,
        user_data: Dict[Any, Any],
        push: bool = True,
    ) -> None:
        if push:
            await self.update_user_data(user_id, user_data)
            return

        raw = await self.redis.hget(self._user_key(), str(user_id))
        if raw:
            user_data.update(self._load(raw))

    async def drop_user_data(self, user_id: int) -> None:
        await self.redis.hdel(self._user_key(), str(user_id))



    async def get_chat_data(self) -> Dict[int, Dict[Any, Any]]:
        raw = await self.redis.hgetall(self._chat_key())
        return {int(k): self._load(v) for k, v in raw.items()} if raw else {}

    async def update_chat_data(self, chat_id: int, data: Dict[Any, Any]) -> None:
        await self.redis.hset(self._chat_key(), str(chat_id), self._dump(data))

    async def drop_chat_data(self, chat_id: int) -> None:
        await self.redis.hdel(self._chat_key(), str(chat_id))



    async def get_conversations(self, name: str) -> Dict[Tuple[int, ...], Any]:
        raw = await self.redis.hgetall(self._conv_key(name))
        if not raw:
            return {}

        result: Dict[Tuple[int, ...], Any] = {}

        for k, v in raw.items():
            try:
                key = tuple(int(x) for x in k.split("_"))
                result[key] = self._load(v)
            except ValueError:
                continue

        return result

    async def update_conversation(
        self,
        name: str,
        key: Tuple[int, ...],
        new_state: Optional[Any],
    ) -> None:
        redis_key = self._conv_key(name)
        str_key = "_".join(map(str, key))

        if new_state is None:
            await self.redis.hdel(redis_key, str_key)
        else:
            await self.redis.hset(redis_key, str_key, self._dump(new_state))



    async def add_chat_session(self, user_id: int, session_id: str) -> None:
        await self.redis.sadd(self._session_set_key(user_id), session_id)

    async def remove_chat_session(self, user_id: int, session_id: str) -> None:
        await self.redis.srem(self._session_set_key(user_id), session_id)

    async def list_chats(
        self,
        user_id: int,
        sort_key: str = "created_at",
        reverse: bool = True,
    ) -> List[Tuple[str, Dict[str, Any]]]:

        sessions = await self.redis.smembers(self._session_set_key(user_id))
        chats: List[Tuple[str, Dict[str, Any]]] = []

        for session_id in sessions:
            meta = await self.redis.hgetall(self._meta_key(user_id, session_id))
            if meta:
                chats.append((session_id, meta))

        return sorted(
            chats,
            key=lambda x: int(x[1].get(sort_key, 0)),
            reverse=reverse,
        )



    async def update_chat_metadata(
        self,
        user_id: int,
        session_id: str,
        metadata: Dict[str, Any],
    ) -> None:
        await self.redis.hset(self._meta_key(user_id, session_id), mapping=metadata)

    async def increment_chat_metadata(
        self,
        user_id: int,
        session_id: str,
        key: str,
        amount: int = 1,
    ) -> None:
        await self.redis.hincrby(self._meta_key(user_id, session_id), key, amount)

    async def get_chat_metadata(
        self,
        user_id: int,
        session_id: str,
    ) -> Dict[str, Any]:
        return await self.redis.hgetall(self._meta_key(user_id, session_id))

    async def delete_chat_metadata(self, user_id: int, session_id: str) -> None:
        await self.redis.delete(self._meta_key(user_id, session_id))



    async def flush(self) -> None:
        await self.redis.aclose()



    async def refresh_bot_data(self, bot_data: Dict) -> None:
        raise NotImplementedError

    async def refresh_chat_data(self, chat_id: int, chat_data: Any) -> None:
        raise NotImplementedError

    async def get_callback_data(self) -> None:
        raise NotImplementedError

    async def update_callback_data(self, data: Any) -> None:
        raise NotImplementedError