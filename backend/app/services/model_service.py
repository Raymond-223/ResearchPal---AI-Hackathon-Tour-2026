from typing import List, Dict, Any, Optional
import os
import requests
from backend.app.core.config import settings

def get_available_models() -> List[Dict[str, Any]]:
    """
    Fetch available models from GenStudio API.
    """
    api_key = os.getenv("GENSTUDIO_API_KEY", settings.genstudio_api_key)
    base_url = os.getenv("GENSTUDIO_BASE_URL", settings.genstudio_base_url)
    
    if not api_key:
        # If no API key, return a default list or empty
        return [
            {"id": "mvp-default", "name": "MVP Default Model (Mock)"}
        ]

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Assuming standard OpenAI-compatible /models endpoint
        url = f"{base_url.rstrip('/')}/models"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Expecting {"data": [{"id": "model-id", ...}, ...]}
            models = data.get("data", [])
            return models
        else:
            print(f"GenStudio API Error: {response.status_code} - {response.text}")
            return [{"id": "error", "name": f"Error: {response.status_code}"}]
            
    except Exception as e:
        print(f"Error fetching models from GenStudio: {e}")
        return [{"id": "connection-error", "name": "Connection Error"}]

def call_genstudio_chat(messages: List[Dict[str, str]], model: str) -> str:
    """
    Call GenStudio Chat Completion API.
    """
    api_key = os.getenv("GENSTUDIO_API_KEY", settings.genstudio_api_key)
    base_url = os.getenv("GENSTUDIO_BASE_URL", settings.genstudio_base_url)
    
    if not api_key:
        raise ValueError("GENSTUDIO_API_KEY not found")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    
    url = f"{base_url.rstrip('/')}/chat/completions"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_genstudio_chat_stream(messages: List[Dict[str, str]], model: str):
    """
    Call GenStudio Chat Completion API with streaming support.
    Yields chunks of the response as they become available.
    """
    import uuid
    
    api_key = os.getenv("GENSTUDIO_API_KEY", settings.genstudio_api_key)
    base_url = os.getenv("GENSTUDIO_BASE_URL", settings.genstudio_base_url)
    
    if not api_key:
        raise ValueError("GENSTUDIO_API_KEY not found")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "stream": True
    }
    
    url = f"{base_url.rstrip('/')}/chat/completions"
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()
        
        # Parse SSE stream
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data.strip() == '[DONE]':
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"[Error: {str(e)}]"