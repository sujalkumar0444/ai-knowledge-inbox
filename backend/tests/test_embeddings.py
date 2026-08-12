import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.embeddings import LocalTfidfEmbedder, cosine_similarity


def test_embed_returns_one_vector_per_text():
    embedder = LocalTfidfEmbedder()
    texts = ["cats are animals", "dogs are animals too", "the stock market fell today"]
    vectors = embedder.embed(texts)
    assert len(vectors) == 3
    assert all(len(v) > 0 for v in vectors)


def test_embed_empty_list_returns_empty():
    embedder = LocalTfidfEmbedder()
    assert embedder.embed([]) == []


def test_similar_texts_score_higher_than_unrelated_text():
    embedder = LocalTfidfEmbedder()
    corpus = [
        "Employees get 20 vacation days per year at the company.",
        "The office requires badge access after 9pm on weekdays.",
        "Bananas are a good source of potassium and fiber.",
    ]
    vectors = embedder.embed(corpus)

    query_vector = embedder.embed_query("How many vacation days do I get?", corpus)

    sim_vacation = cosine_similarity(query_vector, vectors[0])
    sim_badge = cosine_similarity(query_vector, vectors[1])
    sim_banana = cosine_similarity(query_vector, vectors[2])

    assert sim_vacation > sim_banana
    assert sim_vacation > sim_badge


def test_cosine_similarity_identical_vectors_is_one():
    v = [1.0, 2.0, 3.0]
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_similarity_handles_empty_vectors():
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0], []) == 0.0
