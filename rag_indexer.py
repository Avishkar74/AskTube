from __future__ import annotations

import hashlib
from typing import Dict, List

from config import settings
from rag_chunker import chunk_transcript
from rag_embeddings import embed_texts, get_embedding_model
from rag_faiss_store import FaissVectorStore


def _hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def index_transcript(video_id: str, transcript_text: str, force_reindex: bool = False) -> Dict:
    """Index a transcript into FAISS with metadata for RAG.

    - Chunks transcript with overlap
    - Embeds chunks using SentenceTransformers
    - Stores embeddings in FAISS and metadata in JSON
    - Skips if already indexed with same content unless force_reindex
    """
    if not settings.USE_RAG:
        return {"skipped": True, "reason": "RAG disabled"}

    transcript_hash = _hash_text(transcript_text)

    # Prepare store
    model = get_embedding_model()
    dim = model.get_sentence_embedding_dimension()
    store = FaissVectorStore(dim=dim)
    store.load()

    # Check if already indexed with same hash
    if not force_reindex:
        for md in store.metadata:
            if md.get("video_id") == video_id and md.get("transcript_hash") == transcript_hash:
                return {"skipped": True, "reason": "already indexed", "hash": transcript_hash}

    # If force, or no match, proceed: optionally reset only for this video not trivial; simplest approach: append
    # To avoid duplicate chunks on force, we can filter out existing entries for this video id
    if force_reindex and store.metadata:
        # Rebuild store without this video's entries
        keep_vectors: List[List[float]] = []
        keep_metadata: List[Dict] = []
        # We don't have direct access to raw vectors; thus, pragmatic reset and full rebuild is non-trivial here.
        # For now, reset entire index when force_reindex to keep consistency. In future, persist vectors separately.
        store.reset()

    # Chunk
    chunks = chunk_transcript(transcript_text, settings.CHUNK_TOKEN_TARGET, settings.CHUNK_OVERLAP)
    texts = [c["text"] for c in chunks]

    # Embed
    vectors = embed_texts(texts)

    # Prepare metadata
    metadatas: List[Dict] = []
    for c in chunks:
        metadatas.append({
            "video_id": video_id,
            "chunk_id": c["chunk_id"],
            "token_estimate": c["token_estimate"],
            "transcript_hash": transcript_hash,
            "text": c["text"],
        })

    # Add and save
    store.add(vectors, metadatas)
    store.save()

    return {"indexed": True, "chunks": len(chunks), "hash": transcript_hash}
