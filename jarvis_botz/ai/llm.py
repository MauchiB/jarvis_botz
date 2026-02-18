from __future__ import annotations

from jarvis_botz.config import Config
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langchain_core.messages import SystemMessage
from jarvis_botz.ai.agent_tools import tools
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest, AgentMiddleware, ModelRetryMiddleware
from jarvis_botz.ai.prompts import get_gpt_system_prompt
from typing import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

class PromptContext(TypedDict):
    system_prompt: str
    style: str
    language: str
    max_tokens_limit: int

MSG_KEY = 'messages'
MAX_TOKENS = 3000
Model = Any
Agent = Any

@dynamic_prompt
def llm_dynamic_prompt(request: ModelRequest) -> SystemMessage:
    ctx: PromptContext = request.runtime.context or {}
    prompt = get_gpt_system_prompt().format(**ctx)
    return SystemMessage(content=prompt)


class LLMTrimmingMiddleware(AgentMiddleware): 
    async def abefore_model(self, request: ModelRequest) -> ModelRequest:
         messages = request.get(MSG_KEY, [])
         request[MSG_KEY] = trim_messages(messages=messages, 
                                 max_tokens=MAX_TOKENS, 
                                 strategy='last', 
                                 token_counter=count_tokens_approximately, 
                                 include_system=True)
         return request



class AIGraph:
    def __init__(self, cfg: Config, checkpointer=None, model=None, agent=None) -> None:
        self.cfg = cfg
        self.checkpointer = checkpointer
        self.model = model
        self.agent = agent
        
        


    @classmethod
    async def create(cls, cfg: Config) -> AIGraph:
        checkpointer = await cls._create_checkpointer(cfg=cfg)
        model = cls._create_model(cfg=cfg)
        agent = cls._create_agent(cfg=cfg, model=model, checkpointer=checkpointer)
        
        return cls(cfg=cfg, 
                   checkpointer=checkpointer, 
                   model=model, 
                   agent=agent)
    
    @staticmethod
    async def _create_checkpointer(cfg: Config) -> AsyncRedisSaver:
        checkpointer = AsyncRedisSaver(redis_url=cfg.redis.url,
                                       ttl={'default_ttl':cfg.redis.ttl},
                                       checkpoint_prefix=cfg.redis.history_prefix)
        await checkpointer.setup()
        return checkpointer


    @staticmethod
    def _create_model(cfg: Config) -> Model:
        model = init_chat_model(configurable_fields=('model', 'model_provider', 'temperature'),
                                model='openai/gpt-5-mini',
                                model_provider='openai',
                                api_key=cfg.ai.api_key,
                                base_url=cfg.ai.base_url)
        return model

    @staticmethod
    def _create_agent(cfg: Config, model, checkpointer) -> Agent:
        agent = create_agent(model=model,
                             context_schema=PromptContext,
                             middleware=[llm_dynamic_prompt, LLMTrimmingMiddleware(), ModelRetryMiddleware(max_retries=2)],
                             tools=tools,
                             checkpointer=checkpointer)
        return agent

    


    async def text_generation(self, 
                              msg: BaseMessage, 
                              llm_context:PromptContext,
                              input: Dict[str, List[BaseMessage]], 
                              config: Dict[str, Any]) -> str:
        
        if msg is None:
                raise ValueError('msg must be provided for text generation.')
            
        answer = await self.agent.ainvoke(
            input=input,
            config=config,
            context=llm_context
        )
        
        prepared_answer = answer['messages'][-1].content if answer else 'Ответ не получен ('
        return prepared_answer.strip()
        

    

    async def custom_generation(self, prompt_func: ChatPromptTemplate, **kwargs) -> str:
        prompt = prompt_func(**kwargs)
        response = await self.model.ainvoke(input=prompt.format_messages())
        return response.content.strip()
    

    async def delete_chat(self, session_id: str) -> None:
        await self.checkpointer.adelete_thread(thread_id=session_id)


    async def get_history(self, session_id: str) -> List[BaseMessage]:
        data = await self.checkpointer.aget_tuple(config={'configurable': {'thread_id': session_id}})
        return data.checkpoint['channel_values'].get('messages', [])
