import os
import sys
import argparse
import time
import random
from pathlib import Path
from typing import Optional, List

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
			"Missing GOOGLE_API_KEY in environment or .env (also checked GEMINI_API_KEY)."
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


def _build_summarizer(
	model: str,
	api_key: str,
	max_output_tokens: int = 384,
	temperature: float = 0.2,
):
	llm = ChatGoogleGenerativeAI(
		model=model,
		google_api_key=api_key,
		max_output_tokens=max_output_tokens,
		temperature=temperature,
	)
	prompt = PromptTemplate.from_template(
		"""
		You are a precise, concise technical summarizer.
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
	)
	return prompt | llm | StrOutputParser()


def _invoke_with_backoff(
	chain,
	content: str,
	retries: int = 6,
	initial_backoff: float = 2.0,
) -> str:
	for attempt in range(retries):
		try:
			return chain.invoke({"content": content})
		except Exception as e:
			msg = str(e)
			if "429" in msg or "Resource exhausted" in msg:
				sleep_s = initial_backoff * (2 ** attempt) + random.uniform(0, 0.5)
				print(
					f"Rate limited (429). Retrying in {sleep_s:.1f}s... [{attempt+1}/{retries}]"
				)
				time.sleep(sleep_s)
				continue
			raise
	raise RuntimeError("Exceeded retry attempts due to rate limits (429)")


def summarize_text(
	text: str,
	model: str = "gemini-2.0-flash-lite",
	per_chunk_chars: int = 6000,
	max_output_tokens: int = 384,
	retries: int = 6,
	initial_backoff: float = 2.0,
) -> str:
	api_key = _get_api_key()
	chain = _build_summarizer(
		model, api_key, max_output_tokens=max_output_tokens, temperature=0.2
	)

	if per_chunk_chars and len(text) > per_chunk_chars:
		chunks = _chunk_text(text, per_chunk_chars)
		partial_summaries = [
			_invoke_with_backoff(
				chain, c, retries=retries, initial_backoff=initial_backoff
			)
			for c in chunks
		]
		combined = "\n\n".join(partial_summaries)
		return _invoke_with_backoff(
			chain, combined, retries=retries, initial_backoff=initial_backoff
		)
	else:
		return _invoke_with_backoff(
			chain, text, retries=retries, initial_backoff=initial_backoff
		)


def main(argv: Optional[List[str]] = None) -> int:
	parser = argparse.ArgumentParser(description="Summarize a long text using Gemini.")
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
		"--model",
		type=str,
		default="gemini-2.0-flash-lite",
		help="Gemini model name (default: gemini-2.0-flash-lite)",
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
		"--retries",
		type=int,
		default=6,
		help="Number of retries on 429 (default: 6)",
	)
	parser.add_argument(
		"--initial-backoff",
		type=float,
		default=2.0,
		help="Initial backoff seconds for 429 (default: 2.0)",
	)

	args = parser.parse_args(argv)

	input_path = Path(args.input)
	output_path = Path(args.output)
	output_path.parent.mkdir(parents=True, exist_ok=True)

	try:
		text = _read_text(input_path)
		summary = summarize_text(
			text,
			model=args.model,
			per_chunk_chars=args.chunk_chars,
			max_output_tokens=args.max_output_tokens,
			retries=args.retries,
			initial_backoff=args.initial_backoff,
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

