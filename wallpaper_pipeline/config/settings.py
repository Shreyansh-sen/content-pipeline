import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # Flask Configuration
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 2000
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    # # Azure OpenAI Configuration
    # AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT')
    # API_KEY = os.getenv('API_KEY')
    # API_VERSION = os.getenv('API_VERSION', '2025-04-01-preview')
    # DEPLOYMENT_NAME = os.getenv('DEPLOYMENT_NAME', 'gpt-5-mini')

    # Gemini Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/models')

    # Models
    PROMPT_MODEL = os.getenv('PROMPT_MODEL', 'gemini-2.5-flash-lite')
    ADVANCED_MODEL = os.getenv('ADVANCED_MODEL', 'gemini-2.5-pro')
    IMAGE_MODEL = os.getenv('IMAGE_MODEL', 'gemini-3.1-flash-image-preview')
    VIDEO_MODEL = os.getenv('VIDEO_MODEL', 'veo-3.1-generate-preview')
    VIDEO_ASPECT_RATIO = os.getenv('VIDEO_ASPECT_RATIO', '9:16')
    
    # PocketBase Configuration
    POCKETBASE_ADMIN_TOKEN = os.getenv('POCKETBASE_ADMIN_TOKEN')
    POCKETBASE_COLLECTION = os.getenv('POCKETBASE_COLLECTION', 'mantra_god_usecase_mappings')
    
    # Hume AI Configuration (for video & live image generation)
    HUME_APIKEY = os.getenv('HUME_APIKEY', '4a3c0504-b5ef-4f20-a0ba-f226dec9d81f')
    HUME_APISECRET = os.getenv('HUME_APISECRET', '82f56a795639af09fca329c3394d90acdddc291c2a96d60b5896a676692e937e')
    HUME_API_ENDPOINT = os.getenv('HUME_API_ENDPOINT', 'https://api.hume.ai/v0')
    VIDEO_DURATION = 10  # seconds, no sound
