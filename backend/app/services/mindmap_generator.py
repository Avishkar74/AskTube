from ..core.logging import logger
from .llm_backend import auto_select_backend

def generate_mindmap(text: str) -> str:
    """Generate a mermaid.js mindmap from the transcript."""
    try:
        backend = auto_select_backend("ollama")
        prompt = (
            "Create a Mermaid.js mindmap for this content. "
            "Return ONLY the mermaid code block, starting with `mindmap`.\n\n"
            f"{text[:10000]}"
        )
        return backend.generate(prompt)
    except Exception as e:
        logger.error(f"Mindmap generation failed: {e}")
        return "mindmap\n  root((Error))\n    Generation Failed"
