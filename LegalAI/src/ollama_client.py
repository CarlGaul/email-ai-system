#!/usr/bin/env python3
import requests
import json
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

class OllamaClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or Config.OLLAMA_BASE_URL
        self.timeout = 300

    def generate_response(self, model: str, prompt: str, system_prompt: str = "", stream: bool = False):
        """Generate response from Ollama"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": stream,
                "options": {"num_gpu": 999} if Config.GPU_ENABLED else {}
            }
            
            print(f"🔍 DEBUG: Sending request to {self.base_url}/api/generate")
            print(f"🔍 DEBUG: Model: {model}")
            print(f"🔍 DEBUG: Stream: {stream}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                # For streaming, collect all chunks
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                full_response += chunk["response"]
                        except json.JSONDecodeError:
                            continue
                return full_response
            else:
                # For non-streaming, return the response directly
                result = response.json()
                return result.get("response", "")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama request failed: {e}")
            return "Sorry, I'm having trouble connecting to the AI model. Please make sure Ollama is running."
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return "Sorry, an unexpected error occurred while processing your request."
