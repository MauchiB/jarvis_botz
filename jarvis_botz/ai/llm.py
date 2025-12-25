from langchain_gigachat import GigaChat
import requests
from jarvis_botz.config import Config
from langchain_community.chat_message_histories import ChatMessageHistory, RedisChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_agent

from langchain.tools import tool

from langgraph.prebuilt import create_react_agent

import os

import logging
import redis

from telegram import Update
from telegram.ext import ContextTypes

from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from langchain_core.messages import SystemMessage

from jarvis_botz.ai.agent_tools import tools


from langchain.agents.middleware import dynamic_prompt, ModelRequest

logger = logging.getLogger(__name__)
from typing import TypedDict




class PromptContext(TypedDict):
    system_prompt: str
    style: str
    language: str
    max_tokens_limit: int


def get_template():
    template = ChatPromptTemplate.from_template(
        "You are Jarvis Botz, the smartest AI assistant designed by Machi to execute tasks precisely.\n\n"
        "**CONFIGURATION & INSTRUCTIONS:**\n"
        "1. **PRIMARY ROLE:** You must strictly act as a **{system_prompt}**.\n"
        "2. **STYLE/TONE:** Format your entire response strictly following the chosen style: **{style}**.\n"
        "3. **RESPONSE LENGTH:** Your answer **must strictly not exceed** {max_tokens_limit} tokens.\n"
        "4. **LANGUAGE:** Your entire output must be written exclusively in **{language}**.\n\n"

        "Strictly avoid using LaTeX symbols or formatting (like $$, \frac, \times). Use only plain text and standard Markdown for math (e.g., use '*' for multiplication, '/' for division). Render numbers and units simply (e.g., 0.04 SOL)."
        
        "**AGENT CAPABILITIES:**\n"
        "- You have access to external tools and functions. Use them whenever you need up-to-date information or to perform specific tasks.\n"
        "- If the user's request requires a tool, call it immediately. Once you get the result, synthesize the final answer.\n"
        "- Even when using tools, you MUST maintain the role and style defined above.\n\n"
        
        "**TASK:** Following all the rules and constraints listed above, respond to the user's request, referencing the chat history where necessary.")

    return template



@dynamic_prompt
def llm_dynamic_prompt(request: ModelRequest):
    ctx: PromptContext = request.runtime.context
    prompt = get_template().format(**ctx)
    return prompt





class AIGraph:
    def __init__(self, checkpointer, cfg: Config):
        self.cfg = cfg
        self.checkpointer = checkpointer
        self.model, self.agent = self._setup()


    @classmethod
    async def create(cls, cfg: Config):
        checkpointer = AsyncRedisSaver(redis_url=cfg.redis_url,
                                       ttl={'default_ttl':cfg.redis_ttl},
                                       checkpoint_prefix=cfg.redis_history_prefix)
        await checkpointer.setup()

        return cls(checkpointer=checkpointer, cfg=cfg)


    def _setup(self):
        access_token = self.get_access_token()
        model = GigaChat(model="GigaChat", temperature=0.7,
                  access_token=access_token,
                  verify_ssl_certs=False,
                  )
        
        agent = create_react_agent(model=model, tools=tools, checkpointer=self.checkpointer, context_schema=PromptContext)
        
        '''agent = create_agent(model=model,
                             context_schema=PromptContext,
                             middleware=[llm_dynamic_prompt],
                             tools=tools,
                             checkpointer=self.checkpointer)'''

        return model, agent



    def get_access_token(self):
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

        payload={
        'scope': 'GIGACHAT_API_PERS'
        }

        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'eb6b21c5-eb17-430c-9e56-ce024f69ca93',
        'Authorization': f'Basic {self.cfg.base_api_key}'
        }

        response = requests.request("POST", url, headers=headers, data=payload, verify=False)
        access_token = response.json().get("access_token")
        return access_token
    

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


            async for out in self.agent.astream(
                input=input,
                config=config,
                context=llm_context
                ):

                target_key = next((k for k in ['agent', 'model'] if k in out), None)

                if 'tools' in out:
                    print('TOOL')

                if target_key:
                    # Если ключ найден, берем из него последнее сообщение
                    out = out[target_key]['messages'][-1]

                    collected_text += out.content

                    if len(collected_text) > len(last_sent_text): 
                        try:
                            await msg.edit_text(collected_text)
                            last_sent_text = collected_text
                        except Exception as e:
                            pass
            
            return collected_text


    async def name_generation(self, question:str, answer:str) -> str:
        messages = ChatPromptTemplate.from_messages([
    (
        "system",

        "You are a helpful assistant that generates short and relevant chat names based on the conversation between the user and the AI. "
        "The generated name **MUST be in the same language** as the provided User and AI text. " 
        "Provide a concise name that captures the essence of the discussion in **NO MORE THAN 5 WORDS**. "
        "The output must contain ONLY the generated title, with absolutely no quotes, introductions, or extra commentary."
    ),
    (
        "user",
        f"Based on the following interaction, suggest a short and relevant name for the chat:\n\nUser: {question}\nAI: {answer}\n\nChat Name:"
    ),
    ])

        response = await self.model.ainvoke(input=messages.format_messages())
        return response.content.strip()
