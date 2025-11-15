import os
import sys
import argparse
import json
import re
import time
import random
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any

# Suppress FutureWarning from transformers/torch
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

from llm_backend import get_backend, auto_select_backend


SCHEMA_FIELDS = [
    "summary",
    "detailed_notes",
    "key_concepts",
    "examples",
    "memory_tricks",
    "common_mistakes",
    "sticky_notes",
]




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


def _build_prompt(content: str) -> str:
    """Build detailed notes generation prompt."""
    return f"""SYSTEM ROLE:
You are an expert educator and master note-maker. Convert the transcript into structured, clear, exam-ready notes.

CRITICAL: You MUST return ONLY valid, properly formatted JSON. No markdown, no code fences, no extra text.

REQUIRED JSON STRUCTURE:
{{
  "summary": "string here",
  "detailed_notes": "string here",
  "key_concepts": "string here",
  "examples": "string here",
  "memory_tricks": "string here",
  "common_mistakes": "string here",
  "sticky_notes": "string here"
}}

JSON FORMATTING RULES (CRITICAL):
1. Use double quotes for all strings, never single quotes
2. NO trailing commas before closing braces
3. Escape special characters: use \\n for newlines within strings, \\" for quotes
4. Each field value must be a single string (use \\n for line breaks within the string)
5. Do NOT use markdown formatting inside JSON strings (no ** for bold, no # for headers)
6. Start response with {{ and end with }} - nothing else

CONTENT PROCESSING RULES:
1. Identify structure (topics, sections, definitions, repetition, examples, emphases)
2. Break into idea blocks: Definition, Explanation, Example, Exception, Shortcut, Warning, Summary
3. Enhance: add missing explanations, analogies, extra examples, memory hacks, step-by-step logic
4. Prioritize repeated phrases, exam-focused items, definitions/formulas, common struggles
5. Rewrite speech into organized study notes (bullets, headings, numbered steps)
6. Add real-life context only when helpful
7. Keep concise but comprehensive

FIELD CONTENT GUIDELINES:
- summary: 4-7 line high-level overview
- detailed_notes: Expanded multi-section content with bullets (use \\n• for bullets)
- key_concepts: Glossary style definitions separated by \\n\\n
- examples: Original + enriched examples with labels
- memory_tricks: Mnemonics, shortcuts, formulas, step sequences
- common_mistakes: Typical misconceptions, pitfalls, warnings
- sticky_notes: Ultra-short revision bullets (<=12 words each) separated by \\n

TRANSCRIPT:
---
{content}
---

Remember: Output ONLY the JSON object. Start with {{ and end with }}. No other text."""




def _extract_json(raw: str) -> Dict[str, Any]:
    """Robust JSON extraction that tolerates code fences and trailing text.

    Strategy:
    1. Strip ```json fences and any leading/trailing non-JSON text.
    2. Scan for the first balanced top-level JSON object.
    3. If still invalid, attempt to truncate to last complete closing brace.
    4. Try to repair common JSON errors (trailing commas, unescaped quotes).
    5. On failure, raise with helpful diagnostic.
    """
    # Strip fences
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned).strip()

    # Find first opening brace
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("No JSON object start found. Raw begins: " + raw[:120])

    # Balanced brace scan (handle strings properly to ignore braces in strings)
    depth = 0
    end_index = -1
    in_string = False
    escape_next = False

    for i, ch in enumerate(cleaned[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end_index = i
                    break

    if end_index != -1:
        candidate = cleaned[start:end_index + 1]
    else:
        # Fallback: last closing brace
        last_brace = cleaned.rfind('}')
        if last_brace == -1:
            raise ValueError("Unbalanced JSON; no closing brace found. Raw begins: " + raw[:160])
        candidate = cleaned[start:last_brace + 1]

    # Remove trailing junk after final brace if any
    candidate = candidate.strip()

    # Try parsing as-is first
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        # Attempt repairs
        print(f"Initial parse failed: {e}. Attempting repairs...")

        # Repair 1: Remove trailing commas before closing braces/brackets
        repaired = re.sub(r',(\s*[}\]])', r'\1', candidate)

        # Repair 2: Fix unescaped newlines in strings (common LLM error)
        # This is tricky - we'll try to escape newlines inside quoted strings

        try:
            data = json.loads(repaired)
            print("Successfully repaired JSON (removed trailing commas)")
        except json.JSONDecodeError as e2:
            # Last resort: try to extract fields manually with regex
            print(f"Repair failed: {e2}. Attempting field extraction...")
            data = _extract_fields_with_regex(candidate)
            if not data:
                raise ValueError(
                    "Failed to parse JSON after cleanup and repairs. Original error: "
                    + str(e)
                    + " | Candidate snippet begins: "
                    + candidate[:300]
                )

    # Normalize required fields to strings
    for field in SCHEMA_FIELDS:
        val = data.get(field, "")
        if not isinstance(val, str):
            data[field] = str(val)
    return {f: data.get(f, "") for f in SCHEMA_FIELDS}


def _extract_fields_with_regex(text: str) -> Optional[Dict[str, str]]:
    """Last-resort field extraction using regex when JSON parsing fails completely."""
    result = {}

    for field in SCHEMA_FIELDS:
        # Try to match "field": "value" or "field": 'value' patterns
        # This handles multi-line values by using DOTALL
        pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"'
        match = re.search(pattern, text, re.DOTALL)

        if match:
            value = match.group(1)
            # Unescape common escapes
            value = value.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            result[field] = value
        else:
            result[field] = ""

    # Only return if we got at least some fields
    if sum(1 for v in result.values() if v) >= 3:
        print(f"Extracted {sum(1 for v in result.values() if v)}/{len(SCHEMA_FIELDS)} fields via regex")
        return result
    return None


def generate_notes(
    text: str,
    backend_type: str = "ollama",
    model: Optional[str] = None,
    per_chunk_chars: int = 8000,
    max_output_tokens: int = 1024,
    temperature: float = 0.2,
) -> Dict[str, str]:
    """Generate detailed study notes using specified backend.

    Args:
        text: Text to convert into notes
        backend_type: "ollama" or "gemini"
        model: Model name (optional, uses backend defaults)
        per_chunk_chars: Max characters per chunk (0 disables chunking)
        max_output_tokens: Max tokens in response
        temperature: Generation temperature

    Returns:
        Dictionary with note fields
    """
    backend = get_backend(backend_type, model)

    if per_chunk_chars and len(text) > per_chunk_chars:
        chunks = _chunk_text(text, per_chunk_chars)
        partial = []
        for idx, c in enumerate(chunks, 1):
            print(f"[INFO] Processing chunk {idx}/{len(chunks)} (chars={len(c)})")
            prompt = _build_prompt(c)
            raw_response = backend.generate(prompt, max_tokens=max_output_tokens, temperature=temperature)
            partial.append(raw_response)

        combined_prompt_text = "\n\n".join(partial)
        print(f"[INFO] Creating final notes from {len(chunks)} chunks...")
        final_prompt = _build_prompt(combined_prompt_text)
        raw = backend.generate(final_prompt, max_tokens=max_output_tokens, temperature=temperature)
    else:
        prompt = _build_prompt(text)
        raw = backend.generate(prompt, max_tokens=max_output_tokens, temperature=temperature)

    try:
        return _extract_json(raw)
    except ValueError as first_err:
        print("[WARNING] Initial JSON parse failed. Retrying with compact reinforcement prompt...")
        reinforcement = (
            "Return ONLY raw JSON object with keys: "
            + ", ".join(SCHEMA_FIELDS)
            + ". No code fences, no markdown, no commentary."
        )
        combined = reinforcement + "\n\n" + raw[:12000]
        final_prompt = _build_prompt(combined)
        raw2 = backend.generate(final_prompt, max_tokens=max_output_tokens, temperature=temperature)
        try:
            return _extract_json(raw2)
        except ValueError:
            raise first_err


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate detailed study notes JSON from input transcript text.")
    parser.add_argument("--input", type=str, default="input.txt", help="Path to transcript text file")
    parser.add_argument("--output-json", type=str, default="outputs/notes.json", help="Path to write JSON notes")
    parser.add_argument("--output-md", type=str, default="outputs/notes.md", help="Path to write Markdown rendering")
    parser.add_argument(
        "--backend",
        type=str,
        default="ollama",
        choices=["ollama", "gemini"],
        help="LLM backend to use (default: ollama)",
    )
    parser.add_argument("--model", type=str, default=None, help="Model name (default: backend-specific defaults)")
    parser.add_argument("--chunk-chars", type=int, default=8000, help="Max characters per chunk (0 disables)")
    parser.add_argument("--max-output-tokens", type=int, default=1024, help="Max output tokens per call")
    parser.add_argument("--temperature", type=float, default=0.2, help="Generation temperature (default: 0.2)")

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    json_path = Path(args.output_json)
    md_path = Path(args.output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        text = _read_text(input_path)
        notes = generate_notes(
            text,
            backend_type=args.backend,
            model=args.model,
            per_chunk_chars=args.chunk_chars,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
        )
        json_path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")

        # Simple markdown rendering
        md_lines = ["# Study Notes", ""]
        md_lines.append("## Summary\n" + notes["summary"].strip())
        md_lines.append("## Detailed Notes\n" + notes["detailed_notes"].strip())
        md_lines.append("## Key Concepts\n" + notes["key_concepts"].strip())
        md_lines.append("## Examples\n" + notes["examples"].strip())
        md_lines.append("## Memory Tricks\n" + notes["memory_tricks"].strip())
        md_lines.append("## Common Mistakes\n" + notes["common_mistakes"].strip())
        md_lines.append("## Sticky Notes\n" + notes["sticky_notes"].strip())
        md_path.write_text("\n\n".join(md_lines), encoding="utf-8")

        print(f"Saved JSON: {json_path}")
        print(f"Saved Markdown: {md_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
