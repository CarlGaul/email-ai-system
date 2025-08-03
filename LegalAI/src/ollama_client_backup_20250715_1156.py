#!/usr/bin/env python3
"""
Ollama client for communicating with local Ollama instance - ENHANCED FOR PHASE 1
Includes timeout and streaming support.
"""

import requests
import time
import json
from typing import List, Dict, Union, Generator, Any
from config import Config


class OllamaClient:
    """Client for communicating with local Ollama instance - PHASE 1 VERSION"""
    
    def __init__(self, base_url: str = Config.OLLAMA_BASE_URL, timeout: int = 120):
        self.base_url = base_url
        self.available_models = []
        self.timeout = timeout
        self.session = requests.Session()

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10) 
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model["name"] for model in data.get("models", [])]
                return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ DEBUG: Ollama not available: {e}")
            return False
    
    def get_models(self) -> List[str]:
        """Get list of available models in Ollama"""
        if self.is_available():
            return self.available_models
        return []
    
    def generate_response(
        self, 
        model: str, 
        prompt: str, 
        system_prompt: str = "",
        stream: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response using Ollama API - ENHANCED DEBUG VERSION"""
        print(f"🔍 DEBUG: OllamaClient.generate_response called (stream={stream})")
        print(f"🔍 DEBUG: Model: {model}")
        print(f"🔍 DEBUG: Prompt length: {len(prompt)} characters")
        print(f"🔍 DEBUG: System prompt length: {len(system_prompt)} characters")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        
        endpoint = f"{self.base_url}/api/chat"

        try:
            print(f"📤 Sending request to {model}...")
            start_time = time.time()

            response = self.session.post(
                endpoint,
                json=data,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            if stream:
                def generate_chunks():
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if "content" in chunk.get("message", {}):
                                    yield chunk["message"]["content"]
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
                    elapsed_time = time.time() - start_time
                    print(f"⏱️ Stream completed in {elapsed_time:.2f} seconds.")

                return generate_chunks()
            else:
                full_response_content = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if "content" in chunk.get("message", {}):
                                full_response_content += chunk["message"]["content"]
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                elapsed_time = time.time() - start_time
                print(f"⏱️ Full response received in {elapsed_time:.2f} seconds")
                return full_response_content

        except requests.exceptions.Timeout:
            timeout_msg = f"⏰ Request timed out after {self.timeout} seconds. Try a shorter query or check system resources."
            print(f"❌ {timeout_msg}")
            return timeout_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Network error: {str(e)}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            print(error_msg)
            return error_msg

    def test_model_responsiveness(self, model: str) -> Dict[str, Union[bool, float, int, str]]:
        """Test how responsive a model is with a simple query"""
        test_prompt = "What is pregnancy discrimination?"
        start_time = time.time()
        
        try:
            response = self.generate_response(model, test_prompt, stream=False) 
            end_time = time.time()
            
            return {
                "success": True,
                "response_time": end_time - start_time,
                "response_length": len(response),
                "response_preview": response[:100] + "..." if len(response) > 100 else response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
