from langchain_gigachat import GigaChat
import requests
from jarvis_botz.config import Config
from langchain_community.chat_message_histories import ChatMessageHistory, RedisChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model

from langchain.tools import tool

from langgraph.prebuilt import create_react_agent

import os
from langchain_core.messages import BaseMessage

import logging
from typing import List, Dict
import redis

from telegram import Update
from telegram.ext import ContextTypes

from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from langchain_core.messages import SystemMessage

from jarvis_botz.ai.agent_tools import tools
from langchain.agents import create_agent

from langchain.agents.middleware import dynamic_prompt, ModelRequest

from jarvis_botz.ai.prompts import get_gpt_system_prompt, get_name_generation_prompt

from langchain_community.chat_models.yandex import ChatYandexGPT
from langchain_community.embeddings.yandex import YandexGPTEmbeddings

from typing import TypedDict


import asyncio

class PromptContext(TypedDict):
    system_prompt: str
    style: str
    language: str
    max_tokens_limit: int




@dynamic_prompt
def llm_dynamic_prompt(request: ModelRequest):
    ctx: PromptContext = request.runtime.context['context']
    prompt = get_gpt_system_prompt().format(**ctx)
    return SystemMessage(prompt)

'''
def get_model_with_dynamic_prompt(state, config):

    ctx = config["configurable"].get("context", {})

    template = get_gpt_system_prompt()
    formatted_prompt = template.format(**ctx)

    return [SystemMessage(content=formatted_prompt)] + state["messages"]
'''





class AIGraph:
    def __init__(self, checkpointer: AsyncRedisSaver, cfg: Config):
        self.cfg = cfg
        self.checkpointer = checkpointer

        self.model = self._setup_model() 
        self.agent = self._setup_agent() 

        

    @classmethod
    async def create(cls, cfg: Config):
        checkpointer = AsyncRedisSaver(redis_url=cfg.redis_url,
                                       ttl={'default_ttl':cfg.redis_ttl},
                                       checkpoint_prefix=cfg.redis_history_prefix)
        await checkpointer.setup()

        return cls(checkpointer=checkpointer, cfg=cfg)


    def _setup_model(self):
        model = init_chat_model(configurable_fields=('model', 'model_provider', 'temperature'),
                                api_key='',
                                base_url= '', streaming=True)
        return model

    def _setup_agent(self):
        agent = create_agent(model=self.model,
                             context_schema=PromptContext,
                             middleware=[llm_dynamic_prompt],
                             tools=tools,
                             checkpointer=self.checkpointer)

        return agent

    


    async def text_generation(self, msg, llm_context:PromptContext,
                               input: dict, config: dict = None,
                               streaming: bool = False):
        
        if msg is None:
                raise ValueError('msg must be provided for text generation.')
        
        if not streaming:
            answer = await self.agent.ainvoke(
                input=input,
                config=config,
                context=llm_context
            )
            await msg.edit_text(answer.content)
            return answer.content
        

        if streaming:
            last_sent_text = ''
            collected_text = ''


            async for event in self.agent.astream(
                input=input,
                config=config,
                context=llm_context,
                ):

                out = event['model'].get('messages', [])
                if out:
                    out = out[0]
                    collected_text += out.content

                    if len(collected_text) > len(last_sent_text): 
                        try:
                            await msg.edit_text(collected_text)
                            last_sent_text = collected_text
                        except Exception as e:
                            pass

            
            return collected_text


    async def custom_generation(self, prompt_func: ChatPromptTemplate, **kwargs) -> str:
        prompt = prompt_func(**kwargs)
        response = await self.model.ainvoke(input=prompt.format_messages())
        return response.content.strip()
    

    async def delete_chat(self, session_id) -> None:
        await self.checkpointer.adelete_thread(thread_id=session_id)


    async def get_history(self, session_id) -> List[BaseMessage]:
        data = await self.checkpointer.aget_tuple(config={'configurable': {'thread_id': session_id}})
        return data.checkpoint['channel_values'].get('messages', [])
