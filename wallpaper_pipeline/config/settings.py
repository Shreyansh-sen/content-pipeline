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
    VIDEO_DURATION = int(os.getenv('VIDEO_DURATION', '8'))  # Default to 5 seconds
    
    # PocketBase Configuration
    POCKETBASE_ADMIN_TOKEN = os.getenv('POCKETBASE_ADMIN_TOKEN')
    POCKETBASE_COLLECTION = os.getenv('POCKETBASE_COLLECTION', 'mantra_god_usecase_mappings')
    
