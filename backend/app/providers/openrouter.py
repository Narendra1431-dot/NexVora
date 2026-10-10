import os
from ..config import settings
from .base import Provider

class OpenRouterProvider(Provider):
    def __init__(self):
        super().__init__('openrouter',settings.openrouter_base_url,settings.openrouter_api_key,
            os.getenv('OPENROUTER_MODEL','meta-llama/llama-4-scout'))
