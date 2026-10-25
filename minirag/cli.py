import argparse
import sys

from .answer import extractive, with_ollama
from .index import Index

DEFAULT_INDEX = ".minirag.json"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="minirag", description="Search and ask questions over local documents.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("index", help="build an index from a folder or file")
    p.add_argument("path")
    p.add_argument("-o", "--out", default=DEFAULT_INDEX)
    p.add_argument("--chunk-words", type=int, default=120)

    p = sub.add_parser("search", help="show the best matching chunks")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=4)
    p.add_argument("-i", "--index", default=DEFAULT_INDEX)

    p = sub.add_parser("ask", help="answer a question from the documents")
    p.add_argument("question")
    p.add_argument("-k", type=int, default=4)
    p.add_argument("-i", "--index", default=DEFAULT_INDEX)
    p.add_argument("--ollama", metavar="MODEL", help="generate the answer with a local Ollama model")

    args = ap.parse_args(argv)

    if args.cmd == "index":
        idx = Index.build(args.path, max_words=args.chunk_words)
        idx.save(args.out)
        print(f"indexed {len(idx.chunks)} chunks -> {args.out}")
        return 0

    idx = Index.load(args.index)
    query = args.query if args.cmd == "search" else args.question
    hits = idx.search(query, k=args.k)

    if args.cmd == "search":
        for h in hits:
            print(f"{h.score:6.2f}  {h.source}\n        {h.text[:200]}\n")
        return 0 if hits else 1

    if not hits:
        print("No answer found in the indexed documents.")
        return 1
    if args.ollama:
        try:
            print(with_ollama(args.question, hits, model=args.ollama))
        except OSError as e:
            print(f"could not reach Ollama ({e}); falling back to extractive answer", file=sys.stderr)
            print(extractive(args.question, hits))
    else:
        print(extractive(args.question, hits))
    print("\nsources:")
    for source in dict.fromkeys(h.source for h in hits):
        print(" -", source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
