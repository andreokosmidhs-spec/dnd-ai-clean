"""Stub for emergentintegrations — allows server to import without the real package."""
from typing import Any, Optional

class UserMessage:
    def __init__(self, text: str = "", role: str = "user", **kw):
        self.text = text
        self.role = role

class FileContent:
    def __init__(self, *args, **kw):
        pass

class LlmChat:
    def __init__(self, *args, **kw):
        pass
    def with_model(self, *args, **kw):
        return self
    def with_params(self, *args, **kw):
        return self
    async def send_message(self, *args, **kw) -> str:
        raise RuntimeError("emergentintegrations stub — real LLM not available in test env")
