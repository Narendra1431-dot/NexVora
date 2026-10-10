import os
from ..config import settings
from .base import Provider

class GroqProvider(Provider):
    def __init__(self):
        super().__init__('groq','https://api.groq.com/openai/v1',settings.groq_api_key,
            os.getenv('BRAIN_GROQ_MODEL','llama-3.3-70b-versatile'))
