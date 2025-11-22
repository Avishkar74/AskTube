from ..core.logging import logger
from .llm_backend import auto_select_backend

def summarize_text(text: str) -> str:
    """Generate a summary of the transcript."""
    try:
        backend = auto_select_backend("ollama")
        prompt = f"Summarize the following video transcript in 3-5 concise bullet points:\n\n{text[:10000]}"
        return backend.generate(prompt)
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return "Summary generation failed."
