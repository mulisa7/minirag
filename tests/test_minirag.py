from pathlib import Path

from minirag.bm25 import tokenize
from minirag.answer import extractive
from minirag.chunker import chunk
from minirag.cli import main
from minirag.index import Index

DOCS = Path(__file__).resolve().parent.parent / "examples" / "docs"


def test_tokenize_drops_stopwords_and_case():
    assert tokenize("The Sun IS hot") == ["sun", "hot"]


def test_chunks_respect_limit_and_overlap():
    text = " ".join(f"Sentence number {i} has some words." for i in range(30))
    pieces = chunk(text, max_words=20, overlap=1)
    assert len(pieces) > 1
    assert all(len(p.split()) <= 30 for p in pieces)
    # last sentence of a chunk reappears at the start of the next
    assert pieces[0].split(". ")[-1].rstrip(".") in pieces[1]


def test_search_finds_right_document():
    idx = Index.build(str(DOCS))
    top = idx.search("tallest volcano", k=1)[0]
    assert top.source.endswith("solar.md")
    top = idx.search("caffeine in robusta", k=1)[0]
    assert top.source.endswith("coffee.txt")


def test_no_match_returns_nothing():
    idx = Index.build(str(DOCS))
    assert idx.search("kubernetes", k=3) == []


def test_save_and_load_roundtrip(tmp_path):
    idx = Index.build(str(DOCS))
    path = tmp_path / "idx.json"
    idx.save(str(path))
    again = Index.load(str(path))
    assert again.search("hottest planet", k=1)[0].text == idx.search("hottest planet", k=1)[0].text


def test_answer_has_no_repeats_or_unrelated_sentences():
    idx = Index.build(str(DOCS), max_words=25)  # small chunks overlap a lot
    answer = extractive("tallest volcano", idx.search("tallest volcano", k=4))
    assert answer.count("Olympus Mons") == 1
    assert "Venus" not in answer


def test_cli_ask(tmp_path, capsys):
    path = str(tmp_path / "i.json")
    assert main(["index", str(DOCS), "-o", path]) == 0
    assert main(["ask", "Which planet is the hottest?", "-i", path]) == 0
    out = capsys.readouterr().out
    assert "Venus" in out
