from langchain_community.chat_models.gigachat import GigaChat
import requests
from jarvis_botz.config import aiconfig, AiConfig
from langchain_community.chat_message_histories import ChatMessageHistory, RedisChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
import os

import logging
import redis

logger = logging.getLogger(__name__)

class AIGraph:
    def __init__(self, cfg: AiConfig):
        self.cfg = cfg



        self.model = self.initizialize_model()
        self.data = {}



    def _get_session_id(self, session_id: str) -> str:
        server_url = os.getenv("REDIS_URL")
        session_id = str(session_id)
        history = RedisChatMessageHistory(session_id=session_id, url=f'redis://{server_url}:6379')
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
        model = GigaChat(model="GigaChat-2-Max", temperature=0.7,
                  access_token=access_token,
                  verify_ssl_certs=False
                  )
        model = self._prepare_model_with_history(model)
        return model



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




graph = AIGraph(aiconfig)