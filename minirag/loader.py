from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".rst"}


def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit(f"{path}: install pypdf to read PDFs (pip install pypdf)")
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def load_documents(root: str) -> list[tuple[str, str]]:
    """Return (path, text) for every readable file under root."""
    base = Path(root)
    files = [base] if base.is_file() else sorted(base.rglob("*"))
    docs = []
    for p in files:
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES | {".pdf"}:
            text = read_file(p).strip()
            if text:
                docs.append((str(p), text))
    return docs
