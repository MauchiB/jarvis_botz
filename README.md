# Jarvis Botz

Modular Telegram AI bot built with Python, async architecture, Redis, PostgreSQL, and Docker.

---

## Features
- AI chat (LLM responses)
- Multiple chat sessions
- User settings (model, style, language, temperature)
- Payments / token system
- File support (PDF, text, images)
- Redis chat history
- PostgreSQL user data
- Webhook + Web panel
- Docker ready

---

## Tech Stack
- Python 3.12+
- python-telegram-bot
- LangChain / LangGraph
- Redis
- PostgreSQL
- FastAPI (web panel)
- Docker / Docker Compose

---

## Project Structure (simplified)
jarvis_botz/
├── ai/ # LLM logic, prompts, tools
├── bot/ # Telegram handlers, DB, jobs
├── web/ # FastAPI backend + templates
├── app.py # Entry point
└── config.py # Environment config


---

## Installation (Local Dev)

### 1. Clone
git clone <repo>
cd jarvis_botz


### 2. Create venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


## .env Configuration

Create a `.env` file in the project root and define the required environment variables.
These values are used by the bot to connect to external services and control runtime behavior.

### STAGE

Application mode.
`dev` for development, `prod` for production.

### TELEGRAM_BOT_TOKEN

Telegram bot token from BotFather.
Required for the bot to start.

### WEBHOOK_URL

Public HTTPS domain where Telegram will send updates.

### WEBHOOK_PATH

Route path for the webhook endpoint.

### WEBHOOK_PORT

Port that Telegram will connect to.

### WEBAPP_URL

URL of the web panel or web interface.

### POSTGRES_USER

PostgreSQL database username.

### POSTGRES_PASSWORD

PostgreSQL database password.

### POSTGRES_DB

PostgreSQL database name.

### POSTGRES_HOST

PostgreSQL server host.

### POSTGRES_PORT

PostgreSQL server port.

### REDIS_HOST

Redis server host.

### REDIS_PORT

Redis server port.

### REDIS_TTL

Chat history lifetime in seconds.

### REDIS_HISTORY_PREFIX

Prefix for chat history keys in Redis.

### REDIS_METADATA_PREFIX

Prefix for metadata keys in Redis.

### REDIS_CONV_PREFIX

Prefix for conversation keys in Redis.

### REDIS_USER_PREFIX

Prefix for user keys in Redis.

### REDIS_BOT_PREFIX

Prefix for bot keys in Redis.

### REDIS_CHAT_PREFIX

Prefix for chat keys in Redis.

### REDIS_CHAT_SESSIONS_PREFIX

Prefix for chat session keys in Redis.

### AI_API_KEY

API key for the AI provider.

### AI_BASE_URL

Base URL of the language model provider API.

### SERVER_PORT

Internal server port.

### SERVER_HOST

Internal server host address.

### DEV_PROMO

Optional development or debug flag.
