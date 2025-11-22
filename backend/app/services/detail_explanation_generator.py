from ..core.logging import logger
from .llm_backend import auto_select_backend

def generate_notes(text: str) -> str:
    """Generate detailed study notes from the transcript."""
    try:
        backend = auto_select_backend("ollama")
        prompt = f"Create detailed study notes from this transcript. Use Markdown formatting with headers and bullet points:\n\n{text[:15000]}"
        return backend.generate(prompt)
    except Exception as e:
        logger.error(f"Notes generation failed: {e}")
        return "Notes generation failed."
