"""
summarize.py
-------------
Takes raw extracted text and produces a language-simplified summary using
an LLM (Groq's free-tier API, OpenAI-compatible). Handles documents longer
than one model call by chunking, then merging the chunk-level summaries
into one coherent final summary.
"""

import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.3-70b-versatile"  # good quality; use "llama-3.1-8b-instant" for a faster/lighter option
_client = None


def _get_client():
    """Lazy-initialized so importing this module (e.g. to test chunking
    logic) doesn't require the openai package to be installed or the API
    key to be set until an LLM call is actually made."""
    global _client
    if _client is None:
        from openai import OpenAI
        if "GROQ_API_KEY" not in os.environ:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key from "
                "console.groq.com and run: export GROQ_API_KEY=gsk_..."
            )
        _client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
    return _client

# Roughly how many characters to send per chunk. Conservative, to leave
# plenty of room for the model's response within a single call.
CHUNK_CHARS = 8000

CHUNK_SUMMARY_PROMPT = """You are simplifying a document for someone with basic
reading ability (aim for around a Class 8 reading level). Read the text below
and produce:
1. A short summary (3-6 sentences) covering the main points.
2. The key facts as a short bullet list.

Use short sentences and everyday words. Do not add information that isn't in
the text. Do not add a preamble like "Here is the summary" - just give the
summary and bullets directly.

Text:
{chunk}
"""

MERGE_PROMPT = """You are given several partial summaries of different sections
of the same document, in order. Combine them into ONE coherent, simplified
summary of the whole document (aim for around a Class 8 reading level).
Remove repetition between sections. Use short sentences and everyday words.
Structure your output as:

Summary: <one paragraph, 4-8 sentences>

Key Points:
- <bullet>
- <bullet>
...

Partial summaries:
{partials}
"""


def _chunk_text(text: str, chunk_size: int = CHUNK_CHARS) -> list:
    """Simple character-based chunking. Splits on paragraph breaks where
    possible so chunks don't cut mid-sentence too often."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    paragraphs = text.split("\n")
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > chunk_size and current:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks


def _call_llm(prompt: str, max_tokens: int = 800) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": "You simplify and summarize documents in plain, everyday language."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def summarize_text(text: str) -> str:
    """Main entry point: text in -> simplified summary out. Handles
    chunking and merging transparently."""
    chunks = _chunk_text(text)
    print(f"Document split into {len(chunks)} chunk(s) for summarization.")

    if len(chunks) == 1:
        return _call_llm(CHUNK_SUMMARY_PROMPT.format(chunk=chunks[0]), max_tokens=800)

    # Multiple chunks: summarize each, then merge
    partial_summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  Summarizing chunk {i}/{len(chunks)}...")
        partial_summaries.append(_call_llm(CHUNK_SUMMARY_PROMPT.format(chunk=chunk), max_tokens=500))

    print("Merging chunk summaries into one final summary...")
    combined = "\n\n---\n\n".join(
        f"[Section {i+1}]\n{s}" for i, s in enumerate(partial_summaries)
    )
    return _call_llm(MERGE_PROMPT.format(partials=combined), max_tokens=1000)
