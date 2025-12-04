from langchain_community.chat_models.gigachat import GigaChat
import requests
from jarvis_botz.config import aiconfig, AiConfig, config
from langchain_community.chat_message_histories import ChatMessageHistory, RedisChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
import os

import logging
import redis

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class AIGraph:
    def __init__(self, cfg: AiConfig):
        self.cfg = cfg



        self.model, self.base_model = self.initizialize_model()
        self.data = {}



    def _get_session_id(self, session_id: str) -> str:
        if config.stage == 'dev':
            server_url = os.getenv('DEV_HOST')
        else:
            server_url = os.getenv("REDIS_URL")
            
        session_id = str(session_id)
        history = RedisChatMessageHistory(session_id=session_id, url=f'redis://{server_url}:6379', ttl=60*60*24)
        return history
    

    def _get_template(self):
        template = ChatPromptTemplate.from_messages(
            [
                (
                    'system',
                    "You are Jarvis Botz, an advanced AI assistant.\n"
                    "Act strictly as a {style}."
                ),
                ('placeholder', '{history}'),
                ('human', '{input}')
            ]
        )
        return template
    

    def _prepare_model_with_history(self, model):
        template = self._get_template()
        chain = template | model

        run = RunnableWithMessageHistory(chain, 
                                         get_session_history=self._get_session_id,
                                         input_messages_key='input', 
                                         output_messages_key='output',
                                         history_messages_key='history')
        
        
        return run



    def initizialize_model(self):
        access_token = self.get_access_token()
        model = GigaChat(model="GigaChat", temperature=0.7,
                  access_token=access_token,
                  verify_ssl_certs=False,
                  )
        history_model = self._prepare_model_with_history(model)
        return history_model, model



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
    

    async def text_generation(self, msg, update:Update, context:ContextTypes,
                               input: dict, config: dict = None,
                               streaming: bool = False):
        
        if msg is None:
                raise ValueError('msg must be provided for text generation.')
        
        if not streaming:
            answer = await self.model.ainvoke(
                input=input,
                config=config
            )
            await msg.edit_text(answer.content)
            return answer.content
        

        if streaming:
            last_sent_text = ''
            collected_text = ''


            async for out in graph.model.astream(
                input=input,
                config=config
                ):

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
        # 🎯 Добавлено требование сохранить язык
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

        response = await self.base_model.ainvoke(input=messages.format_messages())
        return response.content.strip()






graph = AIGraph(aiconfig)