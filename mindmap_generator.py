import os
import sys
import argparse
import time
import random
import warnings
from pathlib import Path
from typing import Optional, List

# Suppress FutureWarning from transformers/torch
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def _get_api_key() -> str:
    load_dotenv()
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


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def _chunk_text(text: str, max_chars: int) -> List[str]:
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        split = text.rfind("\n\n", start, end)
        if split == -1 or split <= start + int(0.5 * max_chars):
            split = end
        chunks.append(text[start:split].strip())
        start = split
    return [c for c in chunks if c]


def _build_chain(
    model: str, api_key: str, max_output_tokens: int = 512, temperature: float = 0.3
):
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    template = """
You are an expert at creating clear, hierarchical mind maps using Mermaid syntax.

Your task: Analyze the transcript and create a comprehensive mind map using Mermaid mindmap syntax.

IMPORTANT FORMATTING RULES:
1. Start with exactly: mindmap
2. Use proper indentation (2 spaces per level)
3. Root node should be the main topic
4. Branch out to 4-6 major themes
5. Each theme should have 2-4 sub-concepts
6. Keep node text concise (3-7 words max)
7. Use parentheses for multi-word nodes: (Node Text Here)
8. Maximum 4 levels deep
9. NO special characters in node names except parentheses and spaces
10. Output ONLY the Mermaid code - no explanation, no markdown fences

STRUCTURE EXAMPLE:
mindmap
  root((Main Topic))
    Theme 1
      Concept A
      Concept B
    Theme 2
      Concept C
        Detail 1
        Detail 2
      Concept D

CONTENT ANALYSIS GUIDELINES:
- Identify the central topic or learning objective
- Group related concepts into themes
- Show hierarchical relationships
- Highlight key definitions, processes, and examples
- Balance breadth (many themes) with depth (sub-concepts)

TRANSCRIPT:
---
{content}
---

Remember: Output ONLY the Mermaid mindmap code. Start with "mindmap" and use proper indentation.
"""
    prompt = PromptTemplate.from_template(template)
    return prompt | llm | StrOutputParser()


def _invoke_with_backoff(
    chain, content: str, retries: int = 6, initial_backoff: float = 2.0
) -> str:
    for attempt in range(retries):
        try:
            return chain.invoke({"content": content})
        except Exception as e:
            msg = str(e)
            if "429" in msg or "Resource exhausted" in msg:
                sleep_s = initial_backoff * (2**attempt) + random.uniform(0, 0.4)
                print(
                    f"Rate limited (429). Retrying in {sleep_s:.1f}s... [{attempt+1}/{retries}]"
                )
                time.sleep(sleep_s)
                continue
            raise
    raise RuntimeError("Exceeded retry attempts from rate limiting (429)")


def _clean_mermaid_output(raw: str) -> str:
    """Clean up the Mermaid output by removing markdown fences and extra text."""
    # Remove markdown code fences
    cleaned = raw.strip()

    # Remove ```mermaid or ```
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line if it's a fence
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove last line if it's a fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    # Ensure it starts with "mindmap"
    cleaned = cleaned.strip()
    if not cleaned.startswith("mindmap"):
        # Try to find the mindmap line
        lines = cleaned.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("mindmap"):
                cleaned = "\n".join(lines[i:])
                break

    return cleaned.strip()


def generate_mindmap(
    text: str,
    model: str = "gemini-2.0-flash-lite",
    per_chunk_chars: int = 8000,
    max_output_tokens: int = 512,
    retries: int = 6,
    initial_backoff: float = 2.0,
) -> str:
    """Generate a Mermaid mindmap from text.

    Args:
        text: Input text/transcript
        model: Gemini model name
        per_chunk_chars: Max characters per chunk (0 to disable chunking)
        max_output_tokens: Max output tokens per API call
        retries: Number of retry attempts on rate limiting
        initial_backoff: Initial backoff time in seconds

    Returns:
        Mermaid mindmap syntax as string
    """
    api_key = _get_api_key()
    chain = _build_chain(model, api_key, max_output_tokens=max_output_tokens)

    if per_chunk_chars and len(text) > per_chunk_chars:
        # For long content, create a summary first, then mind map from summary
        chunks = _chunk_text(text, per_chunk_chars)
        print(f"Processing {len(chunks)} chunks, will synthesize mind map from key points")

        # Extract key points from each chunk
        key_points = []
        for idx, c in enumerate(chunks, 1):
            print(f"Extracting key points from chunk {idx}/{len(chunks)}")
            summary_prompt = f"Extract 3-5 key points from this content as a bulleted list:\n\n{c}"
            points = _invoke_with_backoff(chain, summary_prompt, retries=retries, initial_backoff=initial_backoff)
            key_points.append(points)

        # Create mind map from combined key points
        combined_text = "\n\n".join(key_points)
        print("Generating mind map from key points...")
        raw = _invoke_with_backoff(chain, combined_text, retries=retries, initial_backoff=initial_backoff)
    else:
        raw = _invoke_with_backoff(chain, text, retries=retries, initial_backoff=initial_backoff)

    return _clean_mermaid_output(raw)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid mind map from input transcript text."
    )
    parser.add_argument(
        "--input", type=str, default="input.txt", help="Path to transcript text file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/mindmap.mmd",
        help="Path to write Mermaid mind map",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.0-flash-lite",
        help="Gemini model name",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=8000,
        help="Max characters per chunk (0 disables)",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=512,
        help="Max output tokens per call",
    )
    parser.add_argument(
        "--retries", type=int, default=6, help="Retries on 429 errors"
    )
    parser.add_argument(
        "--initial-backoff",
        type=float,
        default=2.0,
        help="Initial backoff seconds for rate limit",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        text = _read_text(input_path)
        mindmap = generate_mindmap(
            text,
            model=args.model,
            per_chunk_chars=args.chunk_chars,
            max_output_tokens=args.max_output_tokens,
            retries=args.retries,
            initial_backoff=args.initial_backoff,
        )

        output_path.write_text(mindmap, encoding="utf-8")
        print(f"\nSaved Mermaid mind map: {output_path}")
        print(f"Mind map has {len(mindmap.split(chr(10)))} lines")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
