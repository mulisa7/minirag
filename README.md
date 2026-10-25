# minirag

Ask questions about your own documents from the command line. It's a small version of what LlamaIndex and RAGFlow do: split documents into chunks, rank the chunks against your question, then answer from the best ones.

No dependencies and no API keys. Retrieval is BM25 written from scratch (about 30 lines in `minirag/bm25.py`). For fuller answers you can point it at a local [Ollama](https://ollama.com) model.

## Install

```bash
pip install -e .
pip install pypdf   # only if you want to index PDFs
```

## Use

```bash
minirag index examples/docs
minirag ask "Which planet is the hottest?"
```

```
Venus is the hottest planet because its thick atmosphere traps heat, even though Mercury is nearer the Sun.

sources:
 - examples/docs/solar.md
```

Other commands:

```bash
minirag search "tallest volcano" -k 3         # show matching chunks and scores
minirag ask "..." --ollama llama3.2           # let a local model write the answer
minirag index notes/ -o notes.json            # custom index file
minirag ask "..." -i notes.json
```

Without `--ollama`, the answer is extractive: the sentences from the top chunks that overlap most with the question. With it, the top chunks are sent to the model as context and it is told to answer only from them. If Ollama isn't running it falls back to the extractive answer.

## How it works

```
files -> loader -> chunker -> BM25 index -> top-k chunks -> answer
```

| file | job |
| --- | --- |
| `loader.py` | reads `.txt`, `.md`, `.rst` and `.pdf` |
| `chunker.py` | packs whole sentences into ~120-word chunks with one sentence of overlap |
| `bm25.py` | tokenizer and BM25 scoring |
| `index.py` | builds, searches, saves and loads the index (a JSON list of chunks) |
| `answer.py` | extractive answer and the Ollama call |
| `cli.py` | the `index`, `search` and `ask` commands |

## Limits

- BM25 matches words, not meaning. "automobile" won't find a chunk that only says "car". Swapping in embeddings is the obvious next step.
- The index is rebuilt in memory on every run. Fine for thousands of chunks, not for millions.
- Extractive answers can be a little rough; that's the reason `--ollama` exists.

## Tests

```bash
pip install pytest
python -m pytest
```
