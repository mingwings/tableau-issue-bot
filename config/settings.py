"""
Central configuration settings for Tableau Chatbot
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Paths
SETTINGS = {
    # Data directories
    'METADATA_DIR': BASE_DIR / 'data' / 'parsed_metadata',
    'ISSUES_PATH': BASE_DIR / 'data' / 'historical_issues' / 'issues_export.xlsx',
    'FEEDBACK_DB': BASE_DIR / 'data' / 'feedback_logs' / 'feedback.db',
    'MOCK_SAMPLES_DIR': BASE_DIR / 'data' / 'mock_samples',

    # Configuration files
    'DASHBOARD_REGISTRY': BASE_DIR / 'config' / 'dashboard_registry.json',

    # LLM Configuration
    'LLM_ADAPTER_TYPE': os.getenv('LLM_ADAPTER_TYPE', 'auto'),
    'LLM_TEMPERATURE': float(os.getenv('LLM_TEMPERATURE', '0.7')),
    'LLM_MAX_TOKENS': int(os.getenv('LLM_MAX_TOKENS', '2048')),
    'LLM_TOP_P': float(os.getenv('LLM_TOP_P', '0.95')),

    # LLM API settings
    'LLM_API_KEY': os.getenv('LLM_API_KEY'),
    'LLM_API_URL': os.getenv('LLM_API_URL'),
    'LLM_MODEL': os.getenv('LLM_MODEL', 'gemini-2.5-flash'),
    'EMAIL_ACC': os.getenv('EMAIL_ACC'),
    'KANNON_ID': os.getenv('KANNON_ID', '2010.045'),

    # Context Configuration
    'MAX_HISTORICAL_ISSUES': int(os.getenv('MAX_HISTORICAL_ISSUES', '5')),
    'MAX_CHAT_HISTORY': int(os.getenv('MAX_CHAT_HISTORY', '4')),

    # Parsing Configuration
    'SUPPORTED_WORKBOOK_EXTENSIONS': ['.twb', '.twbx'],
    'SUPPORTED_PREP_EXTENSIONS': ['.tfl', '.tflx'],

    # UI Configuration
    'APP_TITLE': 'Tableau Troubleshooting Assistant',
    'APP_ICON': '📊',
    'LAYOUT': 'wide',

    # Feature flags
    'ENABLE_FEEDBACK': True,
    'ENABLE_CHAT_HISTORY': True,
    'ENABLE_STREAMING': False,  # Not implemented yet
}


def validate_settings() -> bool:
    """
    Validate required settings are present

    Returns:
        True if all required settings are valid, False otherwise
    """
    required_vars = [
        'LLM_API_KEY',
        'LLM_API_URL',
        'EMAIL_ACC'
    ]

    missing = []
    for var in required_vars:
        if not SETTINGS.get(var):
            missing.append(var)

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please configure these in your .env file")
        return False

    return True


def print_settings():
    """Print current settings (for debugging)"""
    print("Current Settings:")
    print("=" * 60)
    for key, value in SETTINGS.items():
        # Don't print sensitive values
        if 'KEY' in key or 'PASSWORD' in key:
            print(f"  {key}: {'*' * 10}")
        else:
            print(f"  {key}: {value}")
    print("=" * 60)


if __name__ == '__main__':
    print("Tableau Chatbot Configuration")
    print("=" * 60)

    if validate_settings():
        print("[OK] All required settings are configured\n")
        print_settings()
    else:
        print("[ERROR] Configuration validation failed")
