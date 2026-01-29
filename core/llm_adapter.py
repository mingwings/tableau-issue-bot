"""
Flexible dbLLM Adapter supporting multiple API formats
Supports: OpenAI-compatible, Custom REST API, Python SDK
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import requests
import warnings

load_dotenv()


class BaseLLMAdapter(ABC):
    """Abstract base for LLM adapters"""

    @abstractmethod
    def generate(self, prompt: str, stream: bool = False, **kwargs) -> str:
        """Generate response from LLM"""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Test API connectivity"""
        pass


class OpenAICompatibleAdapter(BaseLLMAdapter):
    """For OpenAI-compatible APIs (dbLLM format based on AI Tutor pattern)"""

    def __init__(self):
        self.api_key = os.getenv('DB_LLM_API_KEY')
        self.api_url = os.getenv('DB_LLM_API_URL')
        self.model_name = os.getenv('DB_LLM_MODEL', 'gemini-2.5-flash')
        self.email = os.getenv('EMAIL_ACC')
        self.kannon_id = os.getenv('KANNON_ID', '2010.045')

        if not all([self.api_key, self.api_url, self.email]):
            raise ValueError("Missing required environment variables: DB_LLM_API_KEY, DB_LLM_API_URL, EMAIL_ACC")

    def generate(self, prompt: str, stream: bool = False, **kwargs) -> str:
        """
        Generate response using dbLLM OpenAI-compatible endpoint

        Args:
            prompt: The user prompt/message
            stream: Whether to stream response (not implemented yet)
            **kwargs: Additional parameters like system_prompt, temperature, max_tokens

        Returns:
            Generated text response
        """
        system_prompt = kwargs.get('system_prompt', '')
        temperature = kwargs.get('temperature', float(os.getenv('LLM_TEMPERATURE', '0.7')))
        max_tokens = kwargs.get('max_tokens', int(os.getenv('LLM_MAX_TOKENS', '2048')))
        top_p = kwargs.get('top_p', 0.95)

        payload = {
            'email': self.email,
            'apiKey': self.api_key,
            'message': prompt,
            'model_name': self.model_name,
            'params': {
                'temperature': temperature,
                'max_new_token': max_tokens,
                'top_p': top_p
            },
            'system_prompt': system_prompt,
            'bot_name': 'tableau_troubleshooting_assistant',
            'data_classification': 'For Internal Use Only',
            'kannon_id': self.kannon_id
        }

        # Suppress SSL warnings for internal certificates
        warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                verify=False,
                timeout=60
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            raise ConnectionError("dbLLM API request timed out after 60 seconds")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"dbLLM API request failed: {e}")

    def validate_connection(self) -> bool:
        """Test connection to dbLLM"""
        try:
            test_response = self.generate(
                "Hello",
                system_prompt="Respond with 'OK'",
                max_tokens=10
            )
            return bool(test_response)
        except Exception as e:
            print(f"Connection validation failed: {e}")
            return False


class CustomAPIAdapter(BaseLLMAdapter):
    """Fallback for custom REST API format"""

    def __init__(self):
        self.api_key = os.getenv('DB_LLM_API_KEY')
        self.api_url = os.getenv('DB_LLM_API_URL')

        if not all([self.api_key, self.api_url]):
            raise ValueError("Missing required environment variables: DB_LLM_API_KEY, DB_LLM_API_URL")

    def generate(self, prompt: str, stream: bool = False, **kwargs) -> str:
        """Custom API implementation"""
        headers = {'Authorization': f'Bearer {self.api_key}'}
        payload = {
            'prompt': prompt,
            'system_prompt': kwargs.get('system_prompt', ''),
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048)
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json().get('response', response.text)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Custom API request failed: {e}")

    def validate_connection(self) -> bool:
        """Test connection"""
        try:
            test_response = self.generate("Hello", max_tokens=10)
            return bool(test_response)
        except Exception:
            return False


class PythonSDKAdapter(BaseLLMAdapter):
    """For Python SDK if available"""

    def __init__(self):
        try:
            # Placeholder for potential dbLLM SDK
            # import dbllm
            # self.client = dbllm.Client(api_key=os.getenv('DB_LLM_API_KEY'))
            raise ImportError("SDK not installed")
        except ImportError:
            raise NotImplementedError("Python SDK not available. Use OpenAI-compatible or Custom adapter.")

    def generate(self, prompt: str, stream: bool = False, **kwargs) -> str:
        """Generate using SDK"""
        # return self.client.generate(prompt, **kwargs)
        raise NotImplementedError("SDK adapter not implemented")

    def validate_connection(self) -> bool:
        """Validate SDK connection"""
        return False


class LLMAdapterFactory:
    """Factory to select appropriate adapter at runtime"""

    @staticmethod
    def create_adapter(adapter_type: str = 'auto') -> BaseLLMAdapter:
        """
        Create appropriate LLM adapter based on configuration

        Args:
            adapter_type: 'auto', 'openai', 'custom', or 'sdk'

        Returns:
            Initialized LLM adapter
        """
        # Override with environment variable if set
        env_adapter_type = os.getenv('LLM_ADAPTER_TYPE', adapter_type)

        if env_adapter_type == 'auto':
            # Auto-detect based on environment
            if os.getenv('DB_LLM_SDK_AVAILABLE') == 'true':
                adapter_type = 'sdk'
            elif os.getenv('DB_LLM_API_TYPE') == 'custom':
                adapter_type = 'custom'
            else:
                adapter_type = 'openai'
        else:
            adapter_type = env_adapter_type

        adapters = {
            'openai': OpenAICompatibleAdapter,
            'custom': CustomAPIAdapter,
            'sdk': PythonSDKAdapter
        }

        adapter_class = adapters.get(adapter_type.lower())
        if not adapter_class:
            raise ValueError(f"Unknown adapter type: {adapter_type}. Choose from: {list(adapters.keys())}")

        try:
            print(f"Initializing {adapter_type} LLM adapter...")
            adapter = adapter_class()
            return adapter
        except (ValueError, NotImplementedError) as e:
            # If requested adapter fails, try fallback to OpenAI-compatible
            if adapter_type != 'openai':
                print(f"Failed to initialize {adapter_type} adapter: {e}")
                print("Falling back to OpenAI-compatible adapter...")
                return OpenAICompatibleAdapter()
            raise


if __name__ == '__main__':
    # Test the adapter
    print("Testing LLM Adapter...")
    print("=" * 60)

    try:
        adapter = LLMAdapterFactory.create_adapter()

        print("Validating connection...")
        if adapter.validate_connection():
            print("[OK] Connection validated successfully!")

            print("\nTesting generation...")
            response = adapter.generate(
                "What is 2+2?",
                system_prompt="You are a helpful assistant. Answer concisely.",
                max_tokens=50
            )
            print(f"Response: {response[:200]}...")
            print("\n[OK] Adapter test successful!")
        else:
            print("[ERROR] Connection validation failed!")
    except Exception as e:
        print(f"[ERROR] Adapter test failed: {e}")
