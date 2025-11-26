import os
import sys
import argparse
import time
import random
from pathlib import Path
from typing import Optional, List

from llm_backend import get_backend, auto_select_backend




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
	"""Build summarization prompt."""
	return f"""You are a precise, concise technical summarizer.
Summarize the following content for a general audience:

- Provide a brief overview (1-2 sentences)
- Bullet the key points and notable details
- Call out any steps, processes, or tools
- Keep the total under ~250-300 words

Content:
---
{content}
---
"""




def summarize_text(
	text: str,
	backend_type: str = "ollama",
	model: Optional[str] = None,
	per_chunk_chars: int = 6000,
	max_output_tokens: int = 384,
	temperature: float = 0.2,
) -> str:
	"""Summarize text using specified backend.

	Args:
		text: Text to summarize
		backend_type: "ollama" or "gemini"
		model: Model name (optional, uses backend defaults)
		per_chunk_chars: Max characters per chunk (0 disables chunking)
		max_output_tokens: Max tokens in response
		temperature: Generation temperature

	Returns:
		Summary text
	"""
	# Get backend
	backend = get_backend(backend_type, model)

	# Handle chunking for long text
	if per_chunk_chars and len(text) > per_chunk_chars:
		chunks = _chunk_text(text, per_chunk_chars)
		partial_summaries = []

		for i, chunk in enumerate(chunks):
			print(f"[INFO] Summarizing chunk {i+1}/{len(chunks)}...")
			prompt = _build_prompt(chunk)
			summary = backend.generate(prompt, max_tokens=max_output_tokens, temperature=temperature)
			partial_summaries.append(summary)

		# Combine partial summaries
		combined = "\n\n".join(partial_summaries)
		print(f"[INFO] Creating final summary from {len(chunks)} chunks...")
		final_prompt = _build_prompt(combined)
		return backend.generate(final_prompt, max_tokens=max_output_tokens, temperature=temperature)
	else:
		# Single chunk
		prompt = _build_prompt(text)
		return backend.generate(prompt, max_tokens=max_output_tokens, temperature=temperature)


def main(argv: Optional[List[str]] = None) -> int:
	parser = argparse.ArgumentParser(description="Summarize a long text using LLM backend.")
	parser.add_argument(
		"--input",
		type=str,
		default="input.txt",
		help="Path to input text file (default: input.txt)",
	)
	parser.add_argument(
		"--output",
		type=str,
		default="outputs/summary.txt",
		help="Path to write the summary (default: outputs/summary.txt)",
	)
	parser.add_argument(
		"--backend",
		type=str,
		default="ollama",
		choices=["ollama", "gemini"],
		help="LLM backend to use (default: ollama)",
	)
	parser.add_argument(
		"--model",
		type=str,
		default=None,
		help="Model name (default: backend-specific defaults)",
	)
	parser.add_argument(
		"--chunk-chars",
		type=int,
		default=6000,
		help="Optional max characters per chunk for long inputs (0 disables)",
	)
	parser.add_argument(
		"--max-output-tokens",
		type=int,
		default=384,
		help="Max output tokens per call (default: 384)",
	)
	parser.add_argument(
		"--temperature",
		type=float,
		default=0.2,
		help="Generation temperature (default: 0.2)",
	)

	args = parser.parse_args(argv)

	input_path = Path(args.input)
	output_path = Path(args.output)
	output_path.parent.mkdir(parents=True, exist_ok=True)

	try:
		text = _read_text(input_path)
		summary = summarize_text(
			text,
			backend_type=args.backend,
			model=args.model,
			per_chunk_chars=args.chunk_chars,
			max_output_tokens=args.max_output_tokens,
			temperature=args.temperature,
		)
		output_path.write_text(summary, encoding="utf-8")
		print(summary)
		print(f"\nSaved summary to: {output_path}")
		return 0
	except Exception as e:
		print(f"Error: {e}")
		return 1


if __name__ == "__main__":
	sys.exit(main())

