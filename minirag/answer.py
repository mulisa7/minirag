import json
import urllib.request

from .bm25 import tokenize
from .chunker import split_sentences
from .index import Hit


def extractive(question: str, hits: list[Hit], n: int = 2) -> str:
    """No model: return the sentences from the top chunks that share the most
    words with the question."""
    q = set(tokenize(question))
    sents = [s for h in hits for s in split_sentences(h.text)]
    best = sorted(sents, key=lambda s: len(q & set(tokenize(s))), reverse=True)[:n]
    return " ".join(best) if best else "No answer found in the indexed documents."


def with_ollama(question: str, hits: list[Hit], model: str = "llama3.2", host: str = "http://localhost:11434") -> str:
    context = "\n\n".join(f"[{i + 1}] {h.text}" for i, h in enumerate(hits))
    prompt = (
        "Answer the question using only the context. Cite sources like [1]. "
        "If the context does not contain the answer, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["response"].strip()
