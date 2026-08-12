"""
Chunking strategy.

Approach: fixed-size character windows with overlap, but we snap the
boundary to the nearest sentence/paragraph break within a small lookahead
window instead of cutting mid-sentence. This is a deliberate middle ground:

- Pure fixed-size chunking is simple but frequently slices sentences in
  half, which hurts embedding quality (a half-sentence embeds poorly and
  retrieves poorly).
- Semantic chunking (e.g. splitting by detected topic shifts via an LLM)
  is meaningfully better for long, heterogeneous documents but is overkill
  for short notes/articles and adds cost + latency to ingestion.

Overlap (default 150 chars) exists so that facts sitting right at a chunk
boundary don't get orphaned from their surrounding context in retrieval.

See README "Tradeoff Awareness" for what we'd swap in at scale
(e.g. token-aware chunking with a real tokenizer, or a dedicated chunking
library like langchain's RecursiveCharacterTextSplitter / unstructured.io).
"""
import re

from app.config import settings

_SENTENCE_BOUNDARY = re.compile(r"[.!?]\s+")


def chunk_text(
    text: str,
    chunk_size: int = settings.chunk_size_chars,
    overlap: int = settings.chunk_overlap_chars,
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        if end < text_len:
            # Look for a sentence boundary within the trailing 20% of the
            # window so we don't cut mid-sentence.
            lookback_start = max(start, end - int(chunk_size * 0.2))
            window = text[lookback_start:end]
            matches = list(_SENTENCE_BOUNDARY.finditer(window))
            if matches:
                end = lookback_start + matches[-1].end()

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        start = max(end - overlap, start + 1)  # guarantee forward progress

    return chunks
