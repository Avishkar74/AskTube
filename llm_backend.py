"""
LLM Backend Abstraction Layer

Supports multiple backends:
- Ollama (local, free, unlimited)
- Gemini (cloud, fast, rate limited)

Usage:
    backend = get_backend("ollama", "qwen2.5:7b")
    response = backend.generate("Summarize this text...")
"""
import os
import time
import random
from typing import Optional
from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass


class OllamaBackend(LLMBackend):
    """Ollama local LLM backend."""

    def __init__(self, model: str = "qwen2.5:7b"):
        super().__init__(model)
        self._check_installation()

    def _check_installation(self):
        """Check if Ollama is installed and model is available."""
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise RuntimeError(
                "Ollama Python library not installed. Install with: pip install ollama"
            )

        # Check if Ollama service is running
        try:
            self.ollama.list()
        except Exception as e:
            raise RuntimeError(
                f"Ollama service not running. Start it with: ollama serve\nError: {e}"
            )

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        """Generate text using Ollama."""
        try:
            options = {
                "temperature": temperature,
            }
            if max_tokens:
                options["num_predict"] = max_tokens

            response = self.ollama.generate(
                model=self.model,
                prompt=prompt,
                options=options
            )
            if response is None:
                raise RuntimeError("Ollama returned no response object")
            # Newer ollama client may return a typed object with `.response` attribute
            if isinstance(response, dict):
                if "response" not in response or response["response"] is None:
                    raise RuntimeError("Ollama result missing 'response' field")
                return str(response["response"])
            if hasattr(response, "response"):
                val = getattr(response, "response")
                if val is None:
                    raise RuntimeError("Ollama result attribute 'response' is None")
                return str(val)
            # Fallback: if response is a string, return it directly
            if isinstance(response, str):
                return response
            raise RuntimeError(f"Unexpected Ollama response type: {type(response)}")
        except Exception as e:
            # Check if model not found
            if "model" in str(e).lower() and "not found" in str(e).lower():
                raise RuntimeError(
                    f"Model '{self.model}' not found. Pull it with: ollama pull {self.model}"
                )
            raise

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            self._check_installation()
            return True
        except:
            return False


class GeminiBackend(LLMBackend):
    """Google Gemini API backend."""

    def __init__(self, model: str = "gemini-2.0-flash-lite", api_key: Optional[str] = None):
        super().__init__(model)
        self.api_key = api_key or self._get_api_key()
        self._initialize_client()

    def _get_api_key(self) -> str:
        """Get API key from environment.

        Loads .env from current working directory and searches upward to repo root
        so running the backend from a subfolder still finds the root .env.
        """
        try:
            from dotenv import load_dotenv, find_dotenv
            env_path = find_dotenv(usecwd=True)
            if env_path:
                load_dotenv(env_path)
            else:
                load_dotenv()
        except Exception:
            # If dotenv not present, fallback to raw env only
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
            raise RuntimeError(
                "Missing GOOGLE_API_KEY (also checked GEMINI_API_KEY) in environment/.env."
            )
        return api_key

    def _initialize_client(self):
        """Initialize Gemini client."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.ChatGoogleGenerativeAI = ChatGoogleGenerativeAI
        except ImportError:
            raise RuntimeError(
                "LangChain Google GenAI not installed. Install with: pip install langchain-google-genai"
            )

    def generate(self, prompt: str, max_tokens: Optional[int] = None, temperature: float = 0.3) -> str:
        """Generate text using Gemini with retry logic."""
        llm = self.ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            max_output_tokens=max_tokens or 512,
            temperature=temperature,
        )

        # Retry logic for rate limiting
        retries = 6
        initial_backoff = 2.0

        for attempt in range(retries):
            try:
                response = llm.invoke(prompt)
                return response.content
            except Exception as e:
                msg = str(e)
                if "429" in msg or "Resource exhausted" in msg:
                    sleep_s = initial_backoff * (2**attempt) + random.uniform(0, 0.4)
                    print(f"[WARNING] Rate limited. Retrying in {sleep_s:.1f}s... [{attempt+1}/{retries}]")
                    time.sleep(sleep_s)
                    continue
                raise

        raise RuntimeError("Exceeded retry attempts from rate limiting (429)")

    def is_available(self) -> bool:
        """Check if Gemini is available."""
        try:
            self._get_api_key()
            return True
        except:
            return False


def get_backend(backend_type: str = "ollama", model: Optional[str] = None, api_key: Optional[str] = None) -> LLMBackend:
    """Get LLM backend instance.

    Args:
        backend_type: Type of backend ("ollama" or "gemini")
        model: Model name (optional, uses defaults)
        api_key: API key for cloud backends (optional)

    Returns:
        LLMBackend instance

    Examples:
        >>> backend = get_backend("ollama", "qwen2.5:7b")
        >>> response = backend.generate("Summarize this...")

        >>> backend = get_backend("gemini", "gemini-2.0-flash-lite")
        >>> response = backend.generate("Create notes...")
    """
    backend_type = backend_type.lower()

    if backend_type == "ollama":
        model = model or "qwen2.5:7b"
        return OllamaBackend(model)

    elif backend_type == "gemini":
        model = model or "gemini-2.0-flash-lite"
        return GeminiBackend(model, api_key)

    else:
        raise ValueError(f"Unknown backend type: {backend_type}. Use 'ollama' or 'gemini'")


def auto_select_backend(preferred: str = "ollama", model: Optional[str] = None) -> LLMBackend:
    """Automatically select best available backend.

    Args:
        preferred: Preferred backend to try first
        model: Model name (optional)

    Returns:
        First available backend
    """
    backends_to_try = [preferred]
    if preferred == "ollama":
        backends_to_try.append("gemini")
    else:
        backends_to_try.append("ollama")

    for backend_type in backends_to_try:
        try:
            backend = get_backend(backend_type, model)
            if backend.is_available():
                print(f"[INFO] Using {backend_type} backend with model: {backend.model}")
                return backend
        except Exception as e:
            print(f"[WARNING] {backend_type} backend not available: {e}")
            continue

    raise RuntimeError("No LLM backend available. Install Ollama or set GOOGLE_API_KEY")


if __name__ == "__main__":
    # Test backends
    print("Testing LLM Backends\n" + "="*60)

    # Test Ollama
    try:
        print("\n[1] Testing Ollama...")
        ollama_backend = get_backend("ollama", "qwen2.5:7b")
        response = ollama_backend.generate("Say hello in one sentence.")
        print(f"Response: {response[:100]}...")
        print("[OK] Ollama working!")
    except Exception as e:
        print(f"[ERROR] Ollama failed: {e}")

    # Test Gemini
    try:
        print("\n[2] Testing Gemini...")
        gemini_backend = get_backend("gemini")
        response = gemini_backend.generate("Say hello in one sentence.")
        print(f"Response: {response[:100]}...")
        print("[OK] Gemini working!")
    except Exception as e:
        print(f"[ERROR] Gemini failed: {e}")

    # Test auto-select
    try:
        print("\n[3] Testing auto-select...")
        backend = auto_select_backend("ollama")
        response = backend.generate("Say hello in one sentence.")
        print(f"Response: {response[:100]}...")
        print("[OK] Auto-select working!")
    except Exception as e:
        print(f"[ERROR] Auto-select failed: {e}")
