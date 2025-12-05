import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')

# Validation Settings
MAX_SUBJECT_LENGTH = int(os.getenv('MAX_SUBJECT_LENGTH', '100'))

# Security Settings
CHECK_API_KEYS = os.getenv('CHECK_API_KEYS', 'true').lower() == 'true'
CHECK_SENSITIVE_DATA = os.getenv('CHECK_SENSITIVE_DATA', 'true').lower() == 'true'

# Format Settings
ENFORCE_CONVENTIONAL_COMMITS = os.getenv('ENFORCE_CONVENTIONAL_COMMITS', 'true').lower() == 'true'
ENFORCE_LENGTH_LIMIT = os.getenv('ENFORCE_LENGTH_LIMIT', 'true').lower() == 'true'