import asyncio
from asyncio.log import logger
import json
from telegram import Update, Message
from jarvis_botz.utils import check_user, control_tokens, format_user_settings
from jarvis_botz.bot.contexttypes import CustomTypes
from jarvis_botz.bot.jobs import grade_poll_handler, reschedule_inactive_message_job
from jarvis_botz.bot.keyboard_format import PROMPT_CONFIGURATION
from jarvis_botz.bot.keyboards import loading_texts
from jarvis_botz.utils import initialize_new_chat_session
from langchain_core.messages import HumanMessage
from PIL import Image
import time
from typing import Any, Dict, Optional, Tuple
from io import BytesIO
import base64
import random
from langchain_community.document_loaders import PyPDFLoader
from tempfile import NamedTemporaryFile
import os


LLMContent = list[dict[str, Any]]


async def get_text_for_llm(update: Update, context: CustomTypes) -> LLMContent:
    msg = update.effective_message
    if msg is None:
        return [{"type": "text", "text": ""}]


    if msg.text:
        return [
            {"type": "text", "text": msg.text}
        ]


    if msg.photo:
        photo = msg.photo[-1]

        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()

        caption = msg.caption or ""

        img = Image.open(BytesIO(img_bytes))
        img.thumbnail((256, 256))

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=75, optimize=True)

        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return [
            {"type": "text", "text": caption},
            {
                "type": "image",
                "base64": encoded,
                "mime_type": "image/jpeg",
            },
        ]


    if msg.document:
        doc = msg.document
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()


        if doc.mime_type == "application/pdf":
            try:
                temp_path = None
                with NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                    temp.write(file_bytes)
                    temp_path = temp.name

                loader = PyPDFLoader(file_path=temp_path)
                docs = loader.load()
                text = "\n".join(d.page_content for d in docs)

                return [{"type": "text", "text": text}]
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)


        if doc.mime_type == "text/plain":
            text = file_bytes.decode("utf-8", errors="ignore")
            return [{"type": "text", "text": text}]


    return [{"type": "text", "text": ""}]





DEFAULT_MODEL = "openai/gpt-5-mini"
DEFAULT_PROVIDER = "openai"
DEFAULT_TEMPERATURE = 0.7
SAFE_EDIT_LIMIT = 4000
TELEGRAM_TEXT_LIMIT = 4096


async def get_chat_params(
    update: Update,
    context: CustomTypes
) -> Dict[str, Any]:
    user_id: int = update.effective_user.id
    session_id: Optional[str] = context.user_data.get("session_id")

    try:
        chat_metadata: Optional[Dict[str, Any]] = (
            await context.chat_repo.get_chat_metadata(
                user_id=user_id,
                session_id=session_id
            )
        )

        if chat_metadata and isinstance(chat_metadata.get("ai_settings"), str):
            chat_metadata["ai_settings"] = json.loads(
                chat_metadata["ai_settings"]
            )
        else:
            chat_metadata = context.user_data

        chat_params: Dict[str, Any] = format_user_settings(
            user_data=chat_metadata.get("ai_settings", {}),
            config_map=PROMPT_CONFIGURATION
        )

        return chat_params

    except Exception as e:
        logger.exception("Error fetching metadata: %s", e)
        return {}



async def prepare_model_input(
    context: CustomTypes,
    chat_params: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    chat_params = chat_params or {}
    session_id: Optional[str] = context.user_data.get("session_id")

    model_config: Dict[str, Any] = {
        "configurable": {
            "thread_id": session_id,
            "model": chat_params.get("model", DEFAULT_MODEL),
            "model_provider": chat_params.get("model_provider", DEFAULT_PROVIDER),
            "temperature": chat_params.get("temperature", DEFAULT_TEMPERATURE),
        }
    }

    model_context: Dict[str, Any] = {
        "style": chat_params.get("style", "Catchy helpful assistant"),
        "system_prompt": chat_params.get(
            "system_prompt",
            "You are a helpful assistant."
        ),
        "max_tokens": chat_params.get("max_tokens", 150),
        "language": chat_params.get("language", "ru"),
        "model": chat_params.get("model", DEFAULT_MODEL),
    }

    return model_config, model_context



async def generate_answer(
    input: str,
    msg: Message,
    context: Dict[str, Any],
    config: Dict[str, Any],
    model: Any,
    streaming: bool = True
) -> Optional[str]:

    try:
        answer: str = await model.text_generation(
            msg=msg,
            llm_context=context,
            input=input,
            config=config,
            streaming=streaming
        )

        if not answer:
            await msg.edit_text("Пустой ответ от модели.")
            return None

        # --- короткий ответ ---
        if len(answer) <= TELEGRAM_TEXT_LIMIT:
            try:
                await msg.edit_text(answer, parse_mode="HTML")
            except Exception:
                await msg.edit_text(
                    answer +
                    "\n\n(Ошибка форматирования, отправлено без HTML)"
                )
            return answer

        # --- длинный ответ ---
        first_part: str = answer[:SAFE_EDIT_LIMIT]
        second_part: str = answer[SAFE_EDIT_LIMIT:]

        try:
            await msg.edit_text(first_part, parse_mode="HTML")
            await msg.reply_text(second_part, parse_mode="HTML")
        except Exception:
            await msg.edit_text(first_part)
            await msg.reply_text(second_part)

        return answer

    except Exception as e:
        logger.exception("Generation error: %s", e)
        await msg.edit_text(
            "Произошла ошибка при генерации ответа. Попробуйте позже."
        )
        return None
    
    
INACTIVE_RESCHEDULE_SECONDS = 60 * 60 * 24
GRADE_POLL_CHANCE = 0.05


async def update_chat_metadata(
    update: Update,
    context: CustomTypes,
    query: str,
    answer: Optional[str],
) -> None:

    is_creating: bool = context.user_data.get("creating_chat", False)
    session_id: Optional[str] = context.user_data.get("session_id")
    chat_repo = context.chat_repo
    user_id: int = update.effective_user.id

    try:
        if is_creating:
            await initialize_new_chat_session(
                update,
                context,
                query=query,
                answer=answer,
                session_id=session_id,
            )

            context.user_data["creating_chat"] = False
            context.user_data["num_chats"] = (
                context.user_data.get("num_chats", 0) + 1
            )
            return

        new_metadata: Dict[str, Any] = {
            "last_interaction": int(time.time()),
            "last_query": query,
            "last_answer": answer,
        }

        await chat_repo.update_chat_metadata(
            user_id=user_id,
            session_id=session_id,
            metadata=new_metadata,
        )

        await chat_repo.increment_chat_metadata(
            user_id=user_id,
            session_id=session_id,
            key="num_messages",
            amount=1,
        )

    except Exception:
        logger.exception("Database update error")



async def prepare_input_model(query: str) -> Dict[str, Any]:
    return {"messages": [HumanMessage(content=query)]}



async def loading_animation(
    msg: Message,
    stop_event: asyncio.Event,
) -> None:

    while not stop_event.is_set():
        await asyncio.sleep(2)

        try:
            await msg.edit_text(random.choice(loading_texts))
        except Exception:
            pass


@check_user(need_chat=True)
async def generate_answer_handler(
    update: Update,
    context: CustomTypes,
) -> None:

    ok, user_tokens, required_tokens = await control_tokens(
        update,
        context,
        text_tokens=1.0,
        image_tokens=5.0,
        document_tokens=5,
    )

    if not ok:
        await update.effective_message.reply_text(
            f"Вы исчерпали лимит токенов. "
            f"Необходимо: {required_tokens}. У вас: {user_tokens}"
        )
        return

    model = context.llm

    msg: Message = await update.effective_message.reply_text(
        random.choice(loading_texts)
    )

    stop_event = asyncio.Event()
    loading_task = asyncio.create_task(
        loading_animation(msg=msg, stop_event=stop_event)
    )

    model_input_raw = await get_text_for_llm(update, context)
    query: str = model_input_raw[0]["text"] if model_input_raw else ""

    model_input = await prepare_input_model(query)

    chat_params = await get_chat_params(update, context)
    model_config, model_context = await prepare_model_input(
        context,
        chat_params=chat_params,
    )

    answer: Optional[str] = await generate_answer(
        input=model_input,
        msg=msg,
        context=model_context,
        config=model_config,
        model=model,
        streaming=False,
    )

    stop_event.set()
    await loading_task

    await update_chat_metadata(
        update,
        context,
        query=query,
        answer=answer,
    )

    await reschedule_inactive_message_job(
        update,
        context,
        INACTIVE_RESCHEDULE_SECONDS,
    )

    if answer and random.random() < GRADE_POLL_CHANCE:
        await grade_poll_handler(
            update=update,
            context=context,
            ai_answer=answer,
        )