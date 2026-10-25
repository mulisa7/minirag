import re


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]


def chunk(text: str, max_words: int = 120, overlap: int = 1) -> list[str]:
    """Pack whole sentences into chunks of about max_words, repeating the last
    `overlap` sentences at the start of the next chunk so answers that straddle
    a boundary are still found."""
    chunks, current, count = [], [], 0
    for sent in split_sentences(text):
        n = len(sent.split())
        if current and count + n > max_words:
            chunks.append(" ".join(current))
            current = current[-overlap:] if overlap else []
            count = sum(len(s.split()) for s in current)
        current.append(sent)
        count += n
    if current:
        chunks.append(" ".join(current))
    return chunks
