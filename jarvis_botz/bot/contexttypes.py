from typing import Generic, TypeVar, Dict, TypeAlias, Any, TypedDict, Optional, Type
from telegram.ext import ContextTypes, CallbackContext, ExtBot
from jarvis_botz.bot.db.user_repo import RedisPersistence, UserRepository
from jarvis_botz.bot.db.schemas import SessionLocal
from jarvis_botz.ai.llm import AIGraph







from dataclasses import dataclass

# Мы указываем Dict в 4-м параметре. Теперь Persistence не будет ругаться.
class CustomTypes(CallbackContext[ExtBot, Dict, Dict, Dict]):

    @property
    def chat_repo(self) -> RedisPersistence:
        return self.bot_data.get('chat_repo')

    @property
    def session_factory(self) -> SessionLocal:
        return self.bot_data.get('session_factory')

    @property
    def llm(self) -> AIGraph:
        return self.bot_data.get('llm')

    def user_repo(self, session) -> UserRepository:
        repo_class = self.bot_data.get('user_repo')
        return repo_class(session)
    