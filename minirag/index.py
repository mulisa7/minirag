import json
from dataclasses import dataclass
from pathlib import Path

from .bm25 import BM25, tokenize
from .chunker import chunk
from .loader import load_documents


@dataclass
class Hit:
    score: float
    source: str
    text: str


class Index:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks  # [{"source": ..., "text": ...}]
        self._bm25 = BM25([tokenize(c["text"]) for c in chunks])

    @classmethod
    def build(cls, root: str, max_words: int = 120) -> "Index":
        chunks = []
        for path, text in load_documents(root):
            for piece in chunk(text, max_words=max_words):
                chunks.append({"source": path, "text": piece})
        if not chunks:
            raise ValueError(f"no .txt/.md/.rst/.pdf text found under {root}")
        return cls(chunks)

    def search(self, query: str, k: int = 4) -> list[Hit]:
        scores = self._bm25.scores(tokenize(query))
        order = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)[:k]
        return [Hit(scores[i], self.chunks[i]["source"], self.chunks[i]["text"]) for i in order if scores[i] > 0]

    def save(self, path: str) -> None:
        Path(path).write_text(json.dumps(self.chunks), encoding="utf-8")

    @classmethod
    def load(cls, path: str) -> "Index":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))
