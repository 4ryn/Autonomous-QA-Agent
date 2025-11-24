import logging
import requests
import json
import os
from typing import Optional, Dict, Any
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM client supporting both Groq and Ollama"""
    
    def __init__(self):
        self.use_groq = os.getenv("USE_GROQ", "False").lower() == "true"
        
        if self.use_groq:
            self._init_groq()
        else:
            self._init_ollama()
    
    def _init_groq(self):
        """Initialize Groq client"""
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env file. Get one from https://console.groq.com/keys")
        
        logger.info(f"Using Groq API with model: {self.model}")
    
    def _init_ollama(self):
        """Initialize Ollama client"""
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self._check_connection()
    
    def _check_connection(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Successfully connected to Ollama")
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.model not in model_names and not any(self.model in name for name in model_names):
                    logger.warning(f"Model '{self.model}' not found. Available models: {model_names}")
                    logger.warning(f"Please run: ollama pull {self.model}")
                else:
                    logger.info(f"Model '{self.model}' is available")
            else:
                logger.error(f"Failed to connect to Ollama: Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            logger.error("Please ensure Ollama is running or use Groq API (set USE_GROQ=True in .env)")
        except Exception as e:
            logger.error(f"Error checking Ollama connection: {str(e)}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """Generate text using configured LLM"""
        if self.use_groq:
            return self._generate_groq(prompt, system_prompt, temperature, max_tokens)
        else:
            return self._generate_ollama(prompt, system_prompt, temperature, max_tokens)
    
    def _generate_groq(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """Generate text using Groq API"""
        try:
            logger.info("Generating response from Groq")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result['choices'][0]['message']['content']
                logger.info(f"Generated {len(generated_text)} characters from Groq")
                return generated_text
            else:
                logger.error(f"Error from Groq: Status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Request to Groq timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating text from Groq: {str(e)}")
            return None
    
    def _generate_ollama(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """Generate text using Ollama"""
        try:
            logger.info("Generating response from Ollama")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                logger.info(f"Generated {len(generated_text)} characters from Ollama")
                return generated_text
            else:
                logger.error(f"Error from Ollama: Status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request to Ollama timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Error generating text from Ollama: {str(e)}")
            return None
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        if self.use_groq:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers=headers,
                    timeout=5
                )
                return response.status_code == 200
            except:
                return False
        else:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            except:
                return False

# For backward compatibility
OllamaClient = LLMClient