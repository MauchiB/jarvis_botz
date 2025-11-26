import os
import dotenv

dotenv.load_dotenv()



class Config:
    def __init__(self):
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")



class AiConfig:
    def __init__(self, model_name: str = None,
                  model_kwargs: dict = None):
        
        self.model_name = "GigaChat-2-Max"
        self.model_kwargs = {}
        self.base_api_key = os.getenv("BASIC_API_KEY")
        self.access_token = None



config = Config()
aiconfig = AiConfig()
