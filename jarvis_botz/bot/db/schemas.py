from sqlalchemy import create_engine, Column, Integer, String, Float, select, BigInteger, Boolean, ForeignKey, DateTime, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import or_
from sqlalchemy.orm import Mapped, mapped_column

import os
from datetime import datetime, timezone


def get_db_engine(cfg):
    engine = create_async_engine(
        url=cfg.postgres_url,
        echo=False
        )
    return engine



async def init_db(engine):
    async with engine.begin() as conn:
        
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


Base = declarative_base()


from typing import TypeAlias
SessionLocal: TypeAlias = sessionmaker[AsyncSession]


class User(Base):
    __tablename__ = 'users'


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    tokens: Mapped[float] = mapped_column(Float, default=10)
    role: Mapped[str] = mapped_column(String, default='user')
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(True), default=datetime.now(timezone.utc))
    last_active_at: Mapped[datetime] = mapped_column(DateTime(True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)

    subsribers = relationship("Sub", back_populates="user")




class Sub(Base):
    __tablename__ = 'subscribers'


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), index=True)
    subscription_start_date: Mapped[datetime] = mapped_column(DateTime(True))
    subscription_end_date: Mapped[datetime] = mapped_column(DateTime(True))
    tokens_purchased: Mapped[float] = mapped_column(Float, default=0)

    user = relationship("User", back_populates="subsribers")