import datetime
import json
from urllib.parse import parse_qsl
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage, AIMessage
from jarvis_botz.bot.db.user_repo import RedisPersistence




@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chat_repo = await RedisPersistence.create(cfg=app.state.cfg)
    yield
    print("Shutting down...")
    if hasattr(app.state, "chat_repo"):
        await app.state.chat_repo.close()




web_app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="jarvis_botz/web/templates")
router = APIRouter(prefix="/api/v1")



def format_timestamp(ts: int) -> str:
    if not ts:
        return "N/A"
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def parse_tma_header(auth_header: str):
    if not auth_header or not auth_header.startswith("tma "):
        return None

    raw_data = auth_header.replace("tma ", "")
    init_data = dict(parse_qsl(raw_data))

    user_json = init_data.get("user")
    if not user_json:
        return None

    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None





@web_app.get("/main")
async def get_main(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}
    )



@router.get("/chats")
async def get_chats(request: Request, authorization: str = Header(None)):
    user_data = parse_tma_header(authorization)
    if not user_data:
        return {"chats": [], "error": "Invalid auth"}

    user_id = user_data.get("id")

    chats = await request.app.state.chat_repo.get_all_chats(
        user_id,
        sort_key="last_interaction",
        reverse=True
    )

    formatted = []

    for session_id, data in chats:
        formatted.append({
            "id": session_id,
            "name": data.get("name", "Новый чат"),
            "lastMsg": data.get("last_answer", "Пустое сообщение"),
            "time": format_timestamp(int(data.get("last_interaction", 0))),
            "messages": data.get("num_messages", 0),
            "icon": "🤖"
        })

    return {"chats": formatted}



@router.post("/select-chat")
async def api_select_chat(request: Request, data: dict):
    user_id = data.get("user_id")
    session_id = data.get("session_id")

    user_store = request.app.state.bot_app.user_data.setdefault(user_id, {})
    user_store["session_id"] = session_id
    user_store["creating_chat"] = False

    return {"status": "success"}


@router.get("/chats/{session_id}/messages")
async def get_messages(request: Request, session_id: str):
    messages = await request.app.state.bot_app.llm.get_history(session_id)
    history = []

    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
            content = (
                msg.content[0].get("text", "???")
                if isinstance(msg.content, list)
                else msg.content
            )
        elif isinstance(msg, AIMessage):
            role = "assistant"
            content = msg.content
        else:
            role = "system"
            content = msg.content

        history.append({
            "role": role,
            "content": content
        })

    return history



@router.delete("/chats/{session_id}")
async def delete_chat(request: Request, session_id: str, user_id: int):
    bot_app = request.app.state.bot_app
    user_store = bot_app.user_data.setdefault(user_id, {})

    if user_store.get("session_id") == session_id:
        user_store["session_id"] = None

    user_store["num_chats"] = max(0, user_store.get("num_chats", 1) - 1)

    await request.app.state.chat_repo.delete_chat_metadata(
        user_id=user_id,
        session_id=session_id
    )
    await bot_app.llm.delete_chat(session_id)

    return {"status": "ok"}





web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


web_app.include_router(router)

