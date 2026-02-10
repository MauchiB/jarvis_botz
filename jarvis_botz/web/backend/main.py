from fastapi import FastAPI, APIRouter, Request, Header
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import datetime
from contextlib import asynccontextmanager
from jarvis_botz import app
from jarvis_botz.bot.db.user_repo import RedisPersistence
from jarvis_botz.bot.contexttypes import CustomApplication

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chat_repo = await RedisPersistence.create(cfg=app.state.cfg)
    yield
    print("Shutting down...")
    await app.state.chat_repo.close()

from langchain_core.messages import HumanMessage, AIMessage

web_app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory='jarvis_botz/web/templates')

router = APIRouter(prefix="/api/v1")

import json
from urllib.parse import parse_qsl





@web_app.get('/main')
async def get_main(request: Request):
    return templates.TemplateResponse(request=request, name='index.html', context={})


    
@router.get('/chats')
async def get_chats(request: Request, authorization: str = Header(None)):
    auth_header = authorization
    if not auth_header or not auth_header.startswith("tma "):
        return {"chats": [], "error": "No auth header"}


    raw_init_data = auth_header.replace("tma ", "")
    init_data_dict = dict(parse_qsl(raw_init_data))
    

    user_json = init_data_dict.get("user")
    if not user_json:
        return {"chats": [], "error": "No user in initData"}


    user_data = json.loads(user_json)
    user_id = user_data.get("id")
    
    chats = await request.app.state.chat_repo.get_all_chats(user_id)


    formatted_chats = []
    
    for session_id, data in chats.items():
        dt = datetime.datetime.fromtimestamp(data.get('last_interaction', 0))
        time_str = dt.strftime("%H:%M")

        formatted_chats.append({
            "id": session_id,
            "name": data.get('name', 'Новый чат'),
            "lastMsg": data.get('last_answer', 'Пустое сообщение'),
            "time": time_str,
            "messages": data.get('num_messages', 0),
            "icon": "🤖"
        })
    

    formatted_chats.sort(key=lambda x: x.get('last_interaction', 0), reverse=True)

    return {"chats": formatted_chats}


import json

@router.post("/select-chat")
async def api_select_chat(request: Request, data: dict):
    user_id = data.get("user_id")
    session_id = data.get("session_id")

    #context.user_data is not directly accessible here, so we use app.state
    #context.user_data == Application.user_data

    request.app.state.bot_app.user_data[user_id]['session_id'] = session_id
    request.app.state.bot_app.user_data[user_id]['creating_chat'] = False
    

    return {"status": "success"}



@router.get("/chats/{session_id}/messages")
async def get_messages(request: Request, session_id: str):

    

    messages = await request.app.state.bot_app.llm.get_history(session_id)

    formatted_history = []
    
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            role = "system"

        formatted_history.append({
            "role": role,
            "content": msg.content
        })
    

    return formatted_history


@router.delete("/chats/{session_id}")
async def delete_chat(request: Request, session_id: str, user_id:int):
    if request.app.state.bot_app.user_data[user_id].get('session_id') == session_id:
        request.app.state.bot_app.user_data[user_id]['session_id'] = None

    request.app.state.bot_app.user_data[user_id]['num_chats'] -= 1

    await request.app.state.chat_repo.delete_chat_metadata(user_id=user_id, session_id=session_id)
    await request.app.state.bot_app.llm.delete_chat(session_id)

    return {"status": "ok"}



web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


web_app.include_router(router)


def start_backend(cfg, bot_app: CustomApplication):
    web_app.state.cfg = cfg
    web_app.state.bot_app = bot_app
    uvicorn.run(web_app)