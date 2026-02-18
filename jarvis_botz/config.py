import os

class RedisConfig:
    def __init__(
        self,
        host: str,
        port: str,
        ttl: int,
        history_prefix: str,
        metadata_prefix: str,
        conv_prefix: str,
        user_prefix: str,
        bot_prefix: str,
        chat_prefix: str,
        chat_sessions_prefix: str,
    ):
        self.host = host
        self.port = port
        self.ttl = ttl
        self.url = f"redis://{host}:{port}"

        self.history_prefix = history_prefix
        self.metadata_prefix = metadata_prefix
        self.conv_prefix = conv_prefix
        self.user_prefix = user_prefix
        self.bot_prefix = bot_prefix
        self.chat_prefix = chat_prefix
        self.chat_sessions_prefix = chat_sessions_prefix



class PostgresConfig:
    def __init__(self, user, password, db, host, port):
        self.url = (
            f"postgresql+asyncpg://"
            f"{user}:{password}@{host}:{port}/{db}"
        )



class TelegramConfig:
    def __init__(self, token, webhook_url, webhook_path, webhook_port, webapp_url, dev_promo):
        self.token = token
        self.webhook_url = webhook_url
        self.webhook_path = webhook_path
        self.webhook_port = webhook_port
        self.webapp_url = webapp_url
        self.dev_promo = dev_promo



class AIConfig:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key
        self.base_url = base_url


class ServerConfig:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        


class Config:
    def __init__(
        self,
        stage: str,
        postgres: PostgresConfig,
        redis: RedisConfig,
        telegram: TelegramConfig,
        ai: AIConfig,
        server: ServerConfig
    ):
        self.stage = stage
        self.postgres = postgres
        self.redis = redis
        self.telegram = telegram
        self.ai = ai
        self.server = server
        
    
    @classmethod
    def from_env(cls):
        postgres = PostgresConfig(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            db=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
        )

        redis = RedisConfig(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            ttl=int(os.getenv("REDIS_TTL")),
            history_prefix=os.getenv("REDIS_HISTORY_PREFIX", "history"),
            metadata_prefix=os.getenv("REDIS_METADATA_PREFIX", "metadata"),
            conv_prefix=os.getenv("REDIS_CONV_PREFIX", "conv"),
            user_prefix=os.getenv("REDIS_USER_PREFIX", "user"),
            bot_prefix=os.getenv("REDIS_BOT_PREFIX", "bot"),
            chat_prefix=os.getenv("REDIS_CHAT_PREFIX", "chat"),
            chat_sessions_prefix=os.getenv("REDIS_CHAT_SESSIONS_PREFIX", "chat_sessions"),
        )

        telegram = TelegramConfig(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            webhook_url=os.getenv("WEBHOOK_URL"),
            webhook_path=os.getenv("WEBHOOK_PATH"),
            webhook_port=os.getenv("WEBHOOK_PORT"),
            webapp_url=os.getenv("WEBAPP_URL"),
            dev_promo=os.getenv("DEV_PROMO")
        )

        ai = AIConfig(
            api_key=os.getenv("AI_API_KEY"),
            base_url=os.getenv("AI_BASE_URL"),
        )
        
        server = ServerConfig(
            host=os.getenv("SERVER_HOST"),
            port=int(os.getenv("SERVER_PORT"))
        
        ) 


        return cls(
            stage=os.getenv("STAGE"),
            postgres=postgres,
            redis=redis,
            telegram=telegram,
            ai=ai,
            server=server
        )
