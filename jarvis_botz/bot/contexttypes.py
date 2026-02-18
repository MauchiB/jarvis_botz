from telegram.ext import CallbackContext, ExtBot, Application
from jarvis_botz.bot.db.user_repo import RedisPersistence, UserRepository
from jarvis_botz.bot.db.schemas import SessionLocal
from jarvis_botz.ai.llm import AIGraph

from typing import Dict, Optional, Type

class CustomApplication(Application):
    llm: Optional[AIGraph] = None
    session_factory: Optional[SessionLocal] = None
    chat_repo: Optional[RedisPersistence] = None
    user_repo_class: Optional[Type[UserRepository]] = None


class CustomTypes(CallbackContext[ExtBot, Dict, Dict, Dict]):
    @property
    def app(self) -> CustomApplication:
        return self.application


    @property
    def chat_repo(self) -> RedisPersistence:
        if not self.application.chat_repo:
            raise RuntimeError("Chat repository is not initialized.")
        
        return self.application.chat_repo

    @property
    def session_factory(self) -> SessionLocal:
        if not self.application.session_factory:
            raise RuntimeError("Session factory is not initialized.")
        
        return self.application.session_factory

    @property
    def llm(self) -> AIGraph:
        if not self.application.llm:
            raise RuntimeError("LLM is not initialized.")
        
        return self.application.llm

    def get_user_repo(self, session) -> UserRepository:
        if not self.application.user_repo_class:
            raise RuntimeError("User repository class is not set.")
        
        repo_class = self.application.user_repo_class
        return repo_class(session)
    