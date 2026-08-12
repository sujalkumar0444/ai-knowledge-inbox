import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_returns_single_chunk():
    text = "This is a short note."
    result = chunk_text(text, chunk_size=800, overlap=150)
    assert result == [text]


def test_long_text_is_split_into_multiple_chunks():
    text = "This is a sentence about topic A. " * 100  # ~3500 chars
    result = chunk_text(text, chunk_size=800, overlap=150)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) > 0


def test_chunks_prefer_sentence_boundaries():
    text = (
        "First sentence is here. Second sentence follows right after. "
        "Third sentence continues the thought. Fourth sentence wraps it up. "
    ) * 10
    result = chunk_text(text, chunk_size=200, overlap=40)
    # Every chunk except possibly the last should end at a sentence boundary
    # (i.e. end with '.', not mid-word).
    for chunk in result[:-1]:
        assert chunk.rstrip().endswith("."), f"Chunk did not end on a sentence: {chunk!r}"


def test_overlap_creates_shared_content_between_adjacent_chunks():
    text = "Sentence number %d provides unique content here. " 
    full_text = "".join(text % i for i in range(60))
    result = chunk_text(full_text, chunk_size=300, overlap=80)
    assert len(result) >= 2
    # Adjacent chunks should share at least some trailing/leading text given overlap.
    first_tail = result[0][-40:]
    second_head = result[1][:200]
    assert any(word in second_head for word in first_tail.split() if len(word) > 4)


def test_no_infinite_loop_on_pathological_input():
    # A single "sentence" with no punctuation at all, longer than chunk_size.
    text = "word " * 500
    result = chunk_text(text, chunk_size=100, overlap=90)
    # Must terminate and make forward progress every iteration.
    assert len(result) > 1
    reconstructed_length = sum(len(c) for c in result)
    assert reconstructed_length > 0


def test_chunks_never_exceed_reasonable_bounds():
    text = "A. " * 2000  # many tiny sentences
    result = chunk_text(text, chunk_size=500, overlap=100)
    for chunk in result:
        # Allow some slack since boundary-snapping can occasionally overshoot
        # slightly, but nothing should be wildly larger than the window.
        assert len(chunk) <= 700
