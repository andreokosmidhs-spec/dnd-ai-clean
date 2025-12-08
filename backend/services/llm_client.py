"""
Singleton OpenAI client for all LLM calls.
Prevents repeated client instantiation and improves connection reuse.
Uses emergentintegrations for Emergent LLM key support.
"""
import os
import logging
import uuid
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

_client = None


def get_openai_client():
    """
    Get or create the singleton OpenAI client.
    Uses emergentintegrations if Emergent LLM key is detected.
    
    Returns:
        OpenAI-compatible client instance
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    global _client
    
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # For Emergent keys, use emergentintegrations
        if api_key.startswith("sk-emergent-"):
            logger.info("🔑 Detected Emergent LLM key, using emergentintegrations")
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create wrapper that makes LlmChat compatible with OpenAI client interface
            class EmergentClientWrapper:
                def __init__(self, api_key):
                    self.api_key = api_key
                    self.chat = self
                    self.completions = self
                
                def create(self, model, messages, **kwargs):
                    # Extract system message and user messages
                    system_msg = next((m['content'] for m in messages if m['role'] == 'system'), "You are a helpful assistant")
                    user_messages = [m for m in messages if m['role'] != 'system']
                    
                    # Create session ID
                    session_id = str(uuid.uuid4())
                    
                    # Initialize LlmChat
                    chat = LlmChat(
                        api_key=self.api_key,
                        session_id=session_id,
                        system_message=system_msg
                    )
                    
                    # Set model (default gpt-4o)
                    chat.with_model("openai", model)
                    
                    # Note: max_tokens not supported by emergentintegrations LlmChat
                    # It uses default token limits from the model
                    
                    # Combine all user messages into one (emergentintegrations handles one message at a time)
                    combined_text = "\n".join([m['content'] for m in user_messages])
                    user_msg = UserMessage(text=combined_text)
                    
                    # Send message - handle async properly in FastAPI context
                    try:
                        loop = asyncio.get_running_loop()
                        # We're in an async context, use nest_asyncio or run in thread
                        import nest_asyncio
                        nest_asyncio.apply()
                        response = asyncio.run(chat.send_message(user_msg))
                    except RuntimeError:
                        # No running loop, safe to use asyncio.run
                        response = asyncio.run(chat.send_message(user_msg))
                    
                    # Convert response to OpenAI format
                    class Choice:
                        def __init__(self, content):
                            self.message = type('obj', (object,), {'content': content})()
                    
                    class Response:
                        def __init__(self, content):
                            self.choices = [Choice(content)]
                    
                    return Response(response)
            
            _client = EmergentClientWrapper(api_key)
        else:
            logger.info("🔑 Using standard OpenAI client")
            from openai import OpenAI
            _client = OpenAI(api_key=api_key)
        
        logger.info("✅ Singleton OpenAI client initialized")
    
    return _client


def reset_client():
    """Reset the singleton client (mainly for testing)"""
    global _client
    _client = None
