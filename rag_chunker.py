import re
from typing import List, Dict
from config import settings


# Rough conversion: words -> tokens (heuristic)
WORD_TOKEN_RATIO = 0.75


def approximate_token_count(text: str) -> int:
    return int(len(text.split()) * WORD_TOKEN_RATIO)


def split_into_sentences(text: str) -> List[str]:
    # Lightweight sentence splitter; replace with nltk/punkt if needed
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    # Merge tiny trailing fragments
    merged: List[str] = []
    for p in parts:
        if not merged:
            merged.append(p)
        elif len(p) < 2:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return [s for s in merged if s]


def chunk_transcript(
    transcript: str,
    target_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> List[Dict]:
    """Chunk transcript into overlapping segments using approximate token sizes."""
    target_tokens = target_tokens or settings.CHUNK_TOKEN_TARGET
    overlap_tokens = overlap_tokens or settings.CHUNK_OVERLAP

    sentences = split_into_sentences(transcript)
    chunks: List[Dict] = []
    cur: List[str] = []
    cur_tokens = 0
    chunk_id = 1

    for sent in sentences:
        sent_tokens = approximate_token_count(sent)
        if cur and cur_tokens + sent_tokens > target_tokens:
            text = " ".join(cur).strip()
            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "token_estimate": cur_tokens,
            })
            chunk_id += 1

            # Overlap tail
            if overlap_tokens > 0:
                tail: List[str] = []
                tail_tokens = 0
                for s in reversed(cur):
                    t = approximate_token_count(s)
                    if tail_tokens + t > overlap_tokens:
                        break
                    tail.insert(0, s)
                    tail_tokens += t
                cur = tail
                cur_tokens = tail_tokens
            else:
                cur = []
                cur_tokens = 0

        cur.append(sent)
        cur_tokens += sent_tokens

    if cur:
        text = " ".join(cur).strip()
        chunks.append({
            "chunk_id": chunk_id,
            "text": text,
            "token_estimate": cur_tokens,
        })

    return chunks
