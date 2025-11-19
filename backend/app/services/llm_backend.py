"""
Local LLM Backend Abstraction (backend-only copy)

Supports:
- Ollama (local)
- Gemini (via langchain-google-genai)

Hardened to handle dict/typed responses from the ollama Python client.
"""
import os
import time
import random
from typing import Optional
from abc import ABC, abstractmethod


class LLMBackend(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:  # noqa: D401
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "qwen2.5:7b"):
        super().__init__(model)
        self._check_installation()

    def _check_installation(self):
        try:
            import ollama  # type: ignore
            self.ollama = ollama
        except ImportError:
            raise RuntimeError("Python package 'ollama' not installed. pip install ollama")
        try:
            self.ollama.list()
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Ollama service not running. Start with 'ollama serve'. Error: {e}")

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens
        resp = self.ollama.generate(model=self.model, prompt=prompt, options=options)
        if resp is None:
            raise RuntimeError("Ollama returned no response")
        if isinstance(resp, dict):
            val = resp.get("response")
            if val is None:
                raise RuntimeError("Ollama result missing 'response'")
            return str(val)
        if hasattr(resp, "response"):
            val = getattr(resp, "response")
            if val is None:
                raise RuntimeError("Ollama result attribute 'response' is None")
            return str(val)
        if isinstance(resp, str):
            return resp
        raise RuntimeError(f"Unexpected Ollama result type: {type(resp)}")

    def is_available(self) -> bool:
        try:
            self._check_installation()
            return True
        except Exception:  # noqa: BLE001
            return False


class GeminiBackend(LLMBackend):
    def __init__(self, model: str = "gemini-2.0-flash-lite", api_key: Optional[str] = None):
        super().__init__(model)
        self.api_key = api_key or self._get_api_key()
        self._initialize_client()

    def _get_api_key(self) -> str:
        try:
            from dotenv import load_dotenv, find_dotenv  # type: ignore
            env_path = find_dotenv(usecwd=True)
            if env_path:
                load_dotenv(env_path)
            else:
                load_dotenv()
        except Exception:
            pass
        api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("google_api_key")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("gemini_api_key")
        )
        if api_key and " " in api_key:
            api_key = api_key.split()[0]
        if not api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY/GEMINI_API_KEY in environment/.env")
        return api_key

    def _initialize_client(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
            self.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
        except ImportError:
            raise RuntimeError("Install langchain-google-genai to use Gemini backend")

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        llm = self.ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            max_output_tokens=max_tokens or 512,
            temperature=temperature,
        )
        retries = 6
        backoff = 2.0
        for attempt in range(retries):
            try:
                r = llm.invoke(prompt)
                return r.content
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if "429" in msg or "Resource exhausted" in msg:
                    time.sleep(backoff * (2 ** attempt) + random.uniform(0, 0.4))
                    continue
                raise
        raise RuntimeError("Exceeded retry attempts for Gemini")

    def is_available(self) -> bool:
        try:
            _ = self._get_api_key()
            return True
        except Exception:  # noqa: BLE001
            return False


def get_backend(backend_type: str = "ollama", model: Optional[str] = None, api_key: Optional[str] = None) -> LLMBackend:
    bt = (backend_type or "").lower()
    if bt == "ollama" or bt == "":
        return OllamaBackend(model or "qwen2.5:7b")
    if bt == "gemini":
        return GeminiBackend(model or "gemini-2.0-flash-lite", api_key)
    raise ValueError(f"Unknown backend: {backend_type}")


def auto_select_backend(preferred: str = "ollama", model: Optional[str] = None) -> LLMBackend:
    order = [preferred, "gemini" if preferred == "ollama" else "ollama"]
    for b in order:
        try:
            inst = get_backend(b, model)
            if inst.is_available():
                return inst
        except Exception:
            continue
    raise RuntimeError("No LLM backend available (Ollama/Gemini)")
