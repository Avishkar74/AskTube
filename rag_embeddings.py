from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer
from config import settings


_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return embeddings for a list of texts.

    Uses batch encoding via SentenceTransformer for efficiency.
    """
    model = get_embedding_model()
    # convert_to_numpy=False keeps Python lists; convert later if needed
    vectors = model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=False, normalize_embeddings=True)
    # Ensure plain python list of lists
    return [list(map(float, v)) for v in vectors]


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
