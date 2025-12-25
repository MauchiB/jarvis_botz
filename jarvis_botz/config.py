import os





import os
from typing import Optional, Dict, Any

import os
from typing import Optional, Dict, Any, Final



DEV_CONFIG = {
    "postgres_user": "user_dev",
    "postgres_password": "pass_dev",
    "postgres_db": "db_dev",
    "postgres_host": "localhost",
    "postgres_port": "5432",
    "redis_host": "localhost",
    "redis_port": "6379",
    "redis_ttl": "3600"
}

class Config:
    telegram_token: str
    stage: str
    

    model_name: Final[str]
    model_kwargs: Dict[str, Any]
    base_api_key: Optional[str]
    access_token: Optional[str]


    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: str
    postgres_db: str
    postgres_url: str


    redis_host: str
    redis_port: str

    redis_url: Optional[str]
    redis_url: Optional[str]
    

    redis_history_prefix: Final[str]
    redis_metadata_prefix: Final[str]


    def __init__(self, 
                 telegram_token: str,
                 stage: str,

                 postgres_user: Optional[str] = None,
                 postgres_password: Optional[str] = None,
                 postgres_db: Optional[str] = None,
                 postgres_host: Optional[str] = None,
                 postgres_port: Optional[str] = None,
                 postgres_url: Optional[str] = None,

                 redis_host: Optional[str] = None,
                 redis_port: Optional[str] = None,
                 # Остальные параметры
                 redis_url: Optional[str] = None,
                 redis_ttl: Optional[str] = None,

                 base_api_key: Optional[str] = None,
                 access_token: Optional[str] = None):
        

            
                      
        """
        Инициализирует объект конфигурации.
        """
        
        # --- 1. Основные параметры ---
        self.telegram_token = telegram_token
        self.stage = stage
        
        is_dev = self.stage == 'dev'
        
        # --- 2. Параметры PostgreSQL (логика: аргумент > ENV > dev default) ---
        self.postgres_user = postgres_user or os.getenv("POSTGRES_USER", "user_dev" if is_dev else None)
        self.postgres_password = postgres_password or os.getenv("POSTGRES_PASSWORD", "pass_dev" if is_dev else None)
        self.postgres_db = postgres_db or os.getenv("POSTGRES_DB", "db_dev" if is_dev else None)
        
        # Для dev устанавливаем 'localhost'
        self.postgres_host = postgres_host or os.getenv("POSTGRES_HOST", "localhost" if is_dev else None)
        self.postgres_port = postgres_port or os.getenv("POSTGRES_PORT", "5432") # Порт часто одинаков


        if self.postgres_user and self.postgres_password and self.postgres_host and self.postgres_db:
            # Используем postgresql+asyncpg для SQLAlchemy 
            self.postgres_url = (
                f"postgresql+asyncpg://"
                f"{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/"
                f"{self.postgres_db}"
            )
        else:
            self.postgres_url = None # Невозможно сформировать корректный URL
            print("Warning: Insufficient PostgreSQL parameters to form a connection URL.")



        # --- 3. Параметры Redis (логика: аргумент > ENV > dev default) ---
        # Для dev устанавливаем 'localhost'
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost" if is_dev else None)
        self.redis_port = redis_port or os.getenv("REDIS_PORT", "6379")
        
        # Использование URL: если явно не задан, формируем из хоста/порта, 
        # или используем переданный redis_url
        self.redis_url = redis_url or (f"redis://{self.redis_host}:{self.redis_port}" if self.redis_host else None)
        self.redis_ttl = 60*60*24

        # Префиксы Redis (константы)
        self.redis_history_prefix = "history"
        self.redis_user_prefix = "user"
        self.redis_bot_prefix = "bot"
        self.redis_chat_prefix = "chat"
        self.redis_conv_prefix = "conv"

        # --- 4. Параметры AI ---
        self.base_api_key = base_api_key if base_api_key is not None else os.getenv("BASIC_API_KEY")
        self.access_token = access_token
        
        # Константы модели
        self.model_name = "GigaChat-2-Max"
        self.model_kwargs = {}
        
        # --- 5. Проверка критических параметров ---
        if not self.telegram_token:
            raise ValueError("Telegram token is not provided.")
        if not self.base_api_key and not self.access_token:
            print("Warning: BASIC_API_KEY is missing. AI token renewal may fail.")