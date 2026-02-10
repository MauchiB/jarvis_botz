from typing import Generic, TypeVar, Dict, TypeAlias, Any, TypedDict, Optional, Type
from telegram.ext import ContextTypes, CallbackContext, ExtBot, Application
from jarvis_botz.bot.db.user_repo import RedisPersistence, UserRepository
from jarvis_botz.bot.db.schemas import SessionLocal
from jarvis_botz.ai.llm import AIGraph







from dataclasses import dataclass

class CustomApplication(Application):
    def __init__(self, *, bot, update_queue, updater, job_queue, update_processor, persistence, context_types, post_init, post_shutdown, post_stop):
        super().__init__(bot=bot, update_queue=update_queue, updater=updater, 
                         job_queue=job_queue, update_processor=update_processor, 
                         persistence=persistence, context_types=context_types, post_init=post_init, 
                         post_shutdown=post_shutdown, post_stop=post_stop)
        

        self.llm: AIGraph = None
        self.session_factory: SessionLocal = None
        self.chat_repo: RedisPersistence = None
        self.user_repo: UserRepository = None

class CustomTypes(CallbackContext[ExtBot, Dict, Dict, Dict]):
    def __init__(self, application, chat_id = None, user_id = None):
        super().__init__(application, chat_id, user_id)


    @property
    def chat_repo(self) -> RedisPersistence:
        return self.application.chat_repo

    @property
    def session_factory(self) -> SessionLocal:
        return self.application.session_factory

    @property
    def llm(self) -> AIGraph:
        return self.application.llm

    def user_repo(self, session) -> UserRepository:
        repo_class = self.application.user_repo
        return repo_class(session)
    