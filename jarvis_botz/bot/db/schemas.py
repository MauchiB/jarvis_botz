from sqlalchemy import BigInteger, Boolean, ForeignKey, DateTime, String, Integer, Enum
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime, timezone
from typing import TypeAlias
from typing import Optional, List
from jarvis_botz.config import Config

def get_db_engine(cfg: Config):
    engine = create_async_engine(
        url=cfg.postgres.url,
        echo=False
        )
    return engine



async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


Base = declarative_base()


SessionLocal: TypeAlias = sessionmaker[AsyncSession]


class User(Base):
    __tablename__ = 'users'


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    tokens: Mapped[int] = mapped_column(Integer, default=10)
    role: Mapped[str] = mapped_column(Enum('user', 'developer', name='role_enum'), default='user')
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(True), default=lambda: datetime.now(timezone.utc))
    last_active_at: Mapped[datetime] = mapped_column(DateTime(True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)

    referral_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), index=True)

    referral: Mapped[Optional["User"]] = relationship(
        'User', 
        remote_side=[id], 
        back_populates='referrals'
    )

    referrals: Mapped[List["User"]] = relationship(
        'User', 
        back_populates='referral'
    )

