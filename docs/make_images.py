"""Draws the explainer cards in docs/images from real minirag output.

Every number, score and answer on the cards is computed by the library when
this script runs, so the cards can't drift from what the tool does.

    pip install pillow
    python docs/make_images.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from minirag.answer import extractive  # noqa: E402
from minirag.bm25 import tokenize  # noqa: E402
from minirag.chunker import chunk, split_sentences  # noqa: E402
from minirag.index import Index  # noqa: E402
from minirag.loader import load_documents  # noqa: E402

OUT = Path(__file__).parent / "images"
OUT.mkdir(exist_ok=True)
DOCS = ROOT / "examples" / "docs"

W, H = 1080, 1350
PAPER, INK, SOFT = "#fdf6e3", "#1d1d2c", "#6b6b80"
CORAL, MUSTARD, TEAL, BLUE, PURPLE, PINK = "#ff6b6b", "#ffd166", "#06d6a0", "#118ab2", "#8e7dff", "#ff9ecd"
NOTE = [MUSTARD, PINK, "#9be7ff", "#b8f2c9", "#d9c7ff"]
FONTS = "C:/Windows/Fonts/"


def font(size, kind="ui"):
    name = {"ui": "segoeui.ttf", "bold": "segoeuib.ttf", "hand": "segoepr.ttf", "handb": "segoeprb.ttf",
            "mono": "consola.ttf", "monob": "consolab.ttf", "emoji": "seguiemj.ttf"}[kind]
    return ImageFont.truetype(FONTS + name, size)


def emoji(d, xy, ch, size=44):
    try:
        d.text(xy, ch, font=font(size, "emoji"), embedded_color=True)
    except Exception:
        pass


def shadow_box(img, box, fill, outline=None, r=22, width=3, offset=7):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle([x0 + offset, y0 + offset, x1 + offset, y1 + offset], r, fill=(29, 29, 44, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    img.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)
    return d


def wrap(text, f, width, d):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=f) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def para(d, x, y, text, f, fill, width, gap=8):
    for line in wrap(text, f, width, d):
        d.text((x, y), line, font=f, fill=fill)
        y += f.size + gap
    return y


def hl_para(d, x, y, text, f, fill, width, hits, hl=MUSTARD, gap=10):
    """Wrap text and put a highlighter behind every word whose token is in `hits`."""
    space = d.textlength(" ", font=f)
    cx = x
    for word in text.split():
        w = d.textlength(word, font=f)
        if cx + w > x + width and cx > x:
            cx, y = x, y + f.size + gap
        if set(tokenize(word)) & hits:
            d.rounded_rectangle([cx - 3, y + 2, cx + w + 3, y + f.size + 8], 6, fill=hl)
        d.text((cx, y), word, font=f, fill=fill)
        cx += w + space
    return y + f.size + gap


def pill(d, x, y, text, fill, fg=INK, f=None):
    f = f or font(24, "bold")
    w = d.textlength(text, font=f) + 36
    d.rounded_rectangle([x, y, x + w, y + 44], 22, fill=fill)
    d.text((x + 18, y + 6), text, font=f, fill=fg)
    return x + w + 12


def sticky(img, x, y, w, h, title, body, color, angle):
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([24, 24, w + 20, h + 20], fill=(29, 29, 44, 60))
    ld.rectangle([16, 16, w + 12, h + 12], fill=color)
    ld.ellipse([w // 2 - 4, 6, w // 2 + 24, 34], fill=CORAL)  # pin
    ld.text((34, 40), title, font=font(30, "handb"), fill=INK)
    yy = 86
    for line in wrap(body, font(24, "hand"), w - 40, ld)[:5]:
        ld.text((34, yy), line, font=font(24, "hand"), fill=INK)
        yy += 34
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(layer, (x, y), layer)


def new_card(step, title, sub, color=CORAL):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for gx in range(0, W, 54):  # faint grid like a notebook
        d.line([gx, 0, gx, H], fill="#f3ead0", width=1)
    for gy in range(0, H, 54):
        d.line([0, gy, W, gy], fill="#f3ead0", width=1)
    pill(d, 60, 56, step, color, fg="white")
    d.text((60, 118), title, font=font(64, "bold"), fill=INK)
    d.text((62, 200), sub, font=font(32, "hand"), fill=SOFT)
    d.text((60, H - 62), "minirag  ·  github.com/mulisa7/minirag", font=font(24, "bold"), fill=SOFT)
    return img, d


def terminal(img, box, lines):
    """lines: list of (text, color)."""
    d = shadow_box(img, box, "#1b1b2b", r=18, width=0)
    x0, y0, x1, _ = box
    for i, c in enumerate((CORAL, MUSTARD, TEAL)):
        d.ellipse([x0 + 22 + i * 30, y0 + 18, x0 + 40 + i * 30, y0 + 36], fill=c)
    y = y0 + 60
    f = font(25, "mono")
    for text, color in lines:
        for ln in wrap(text, f, x1 - x0 - 50, d) or [""]:
            d.text((x0 + 26, y), ln, font=f, fill=color)
            y += 36
    return y


# ------------------------------------------------------------------ data
docs = dict(load_documents(str(DOCS)))
solar = docs[str(DOCS / "solar.md")]
default_idx = Index.build(str(DOCS))
small_idx = Index.build(str(DOCS), max_words=25)


def ask(idx, q, k=4):
    hits = idx.search(q, k=k)
    return hits, extractive(q, hits)


# ------------------------------------------------------------------ 1 hero
img, d = new_card("1 / 6", "Ask your files a question.", "...and get an answer with receipts", CORAL)
emoji(d, (900, 60), "🧾", 70)
sticky(img, 60, 290, 440, 250, "solar.md", "Jupiter is the largest planet. Mercury is the closest planet to the Sun. Venus is the hottest planet...", NOTE[0], -4)
sticky(img, 560, 300, 440, 250, "coffee.txt", "Arabica has a sweeter taste. Espresso is made by forcing hot water through finely ground coffee...", NOTE[1], 3)
d = ImageDraw.Draw(img)
emoji(d, (480, 590), "⬇️", 60)
d.text((560, 605), "minirag index  (once)", font=font(30, "handb"), fill=BLUE)
q = "How many seconds to pull espresso?"
hits, ans = ask(default_idx, q)
src = Path(hits[0].source).relative_to(ROOT).as_posix()
terminal(img, (60, 700, 1020, 1060), [
    (f'$ minirag ask "{q}"', "#ffffff"), ("", "#ffffff"), (ans, "#06d6a0"), ("", "#ffffff"),
    ("sources:", "#9aa0b4"), (f" - {src}", "#ffd166")])
x = 60
for label, col in [("0 dependencies", TEAL), ("0 API keys", MUSTARD), ("BM25 from scratch", PINK), ("runs locally", "#9be7ff")]:
    x = pill(d, x, 1110, label, col)
para(d, 60, 1180,"RAG = find the right text first, then answer from it. Same idea as LlamaIndex and RAGFlow, in about 230 lines.", font(24), SOFT, 960, gap=4)
img.save(OUT / "1_overview.png")

# ------------------------------------------------------------------ 2 chunking
img, d = new_card("2 / 6", "Step 1: chop it up", "the real solar.md, cut into 25-word chunks", TEAL)
chunks = chunk(solar, max_words=25)
y = 270
prev_last = None
for i, c in enumerate(chunks):
    sents = split_sentences(c)
    h = 28 + sum(len(wrap(s + " ", font(24), 800, d)) * 34 for s in sents) + 12
    shadow_box(img, (60, y, 1020, y + h), "white", outline=NOTE[i % 5], width=4, r=16)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, y, 84, y + h], 12, fill=NOTE[i % 5])
    d.text((96, y + 10), f"#{i + 1}", font=font(26, "handb"), fill=INK)
    ty = y + 14
    for s in sents:
        shared = s == prev_last and sents.index(s) == 0
        lines = wrap(s, font(24), 800, d)
        if shared:
            d.rounded_rectangle([140, ty - 2, 960, ty + len(lines) * 34], 8, fill="#fff0b3")
        for ln in lines:
            d.text((150, ty), ln, font=font(24), fill=INK)
            ty += 34
        if shared:
            d.rounded_rectangle([860, y - 18, 1000, y + 14], 14, fill=CORAL)
            d.text((876, y - 16), "repeated", font=font(21, "bold"), fill="white")
    prev_last = sents[-1]
    y += h + 18
d.text((60, y + 4), "Yellow = the sentence is repeated in the next chunk (overlap).", font=font(26, "hand"), fill=CORAL)
d.text((60, y + 46), "Why? An answer on a boundary still lands whole in one chunk.", font=font(26, "hand"), fill=SOFT)
d.text((60, y + 88), "Shrunk to 25 words for the picture. The default is 120.", font=font(26, "hand"), fill=SOFT)
img.save(OUT / "2_chunking.png")

# ------------------------------------------------------------------ 3 scoring
q = "Which planet is the hottest?"
toks = tokenize(q)
img, d = new_card("3 / 6", "Step 2: score every chunk", f'question: "{q}"', BLUE)
d.text((60, 270), "Stopwords dropped. What is left:", font=font(28, "bold"), fill=INK)
x = 60
for t in toks:
    idf = small_idx._bm25.idf.get(t, 0)
    size = 26 + int(idf * 8)
    f = font(size, "bold")
    w = d.textlength(t, font=f) + 40
    d.rounded_rectangle([x, 320, x + w, 320 + size + 34], 20, fill=MUSTARD if idf > 1 else "#e9e2c8")
    d.text((x + 20, 332), t, font=f, fill=INK)
    d.text((x + 20, 332 + size + 6), f"rarity {idf:.2f}", font=font(20), fill=SOFT)
    x += w + 16
d.text((60, 440), "Rare words are worth more, so 'hottest' counts for more than 'planet'.", font=font(26, "hand"), fill=CORAL)

scores = small_idx._bm25.scores(toks)
order = sorted(range(len(scores)), key=lambda i: -scores[i])
top = max(scores)
y = 500
qset = set(toks)
for rank, i in enumerate(order[:4]):
    c = small_idx.chunks[i]
    shadow_box(img, (60, y, 1020, y + 150), "white", outline=INK if rank == 0 else "#d8d2bb", width=4 if rank == 0 else 2, r=16)
    d = ImageDraw.Draw(img)
    hl_para(d, 90, y + 10, c["text"], font(21), INK, 800, qset, gap=6)
    bw = int(520 * scores[i] / top)
    d.rounded_rectangle([90, y + 108, 90 + max(bw, 6), y + 132], 10, fill=TEAL if rank == 0 else "#bfe9dc")
    d.text((90 + max(bw, 6) + 14, y + 102), f"{scores[i]:.2f}", font=font(28, "bold"), fill=INK)
    if rank == 0:
        emoji(d, (930, y + 92), "🏆", 48)
    y += 166
n_zero = sum(1 for s in scores if s == 0)
d.text((60, y + 2), f"{n_zero} of {len(scores)} chunks scored 0.00 (all the coffee ones). Not even invited.", font=font(26, "hand"), fill=SOFT)
d.text((60, y + 44), "The winner also holds the Venus sentence: that's our answer.", font=font(26, "hand"), fill=CORAL)
img.save(OUT / "3_bm25.png")

# ------------------------------------------------------------------ 4 answer
q = "How many seconds to pull espresso?"
qt = set(tokenize(q))
hits = small_idx.search(q, k=4)
sents = list(dict.fromkeys(s for h in hits for s in split_sentences(h.text)))
scored = sorted(((len(qt & set(tokenize(s))), s) for s in sents), key=lambda x: -x[0])
picked = [s for n, s in scored[:2] if n]
img, d = new_card("4 / 6", "Step 3: pick the sentences", f'question: "{q}"', PURPLE)
d.text((60, 270), "Top 4 chunks -> unique sentences -> count shared words:", font=font(28, "bold"), fill=INK)
y = 330
for n, s in scored[:5]:
    win = s in picked
    lines = wrap(s, font(23), 760, d)
    h = 30 + len(lines) * 33
    shadow_box(img, (60, y, 1020, y + h), "#eafff6" if win else "white", outline=TEAL if win else "#d8d2bb", width=4 if win else 2, r=14)
    d = ImageDraw.Draw(img)
    d.ellipse([78, y + h // 2 - 26, 130, y + h // 2 + 26], fill=TEAL if win else "#e4ddc2")
    d.text((96 if n < 10 else 88, y + h // 2 - 20), str(n), font=font(32, "bold"), fill=INK)
    hl_para(d, 150, y + 14, s, font(23), INK, 800, qt, gap=10)
    if win:
        emoji(d, (940, y + h // 2 - 20), "✅", 36)
    y += h + 14
d.text((60, y + 4), "Yellow = words shared with your question. Top 2 with a match win.", font=font(26, "hand"), fill=SOFT)
y += 60
shadow_box(img, (60, y, 1020, y + 190), PAPER, outline=INK, width=4, r=22)
d = ImageDraw.Draw(img)
d.text((90, y + 14), "Final answer", font=font(26, "handb"), fill=CORAL)
para(d, 90, y + 56, " ".join(picked), font(27, "bold"), INK, 900, gap=8)
y += 220
d.text((60, y), "Or hand the chunks to a local LLM (--ollama)", font=font(30, "bold"), fill=INK)
prompt = ("Answer the question using only the context. Cite sources like [1]. "
          "If the context does not contain the answer, say so.")
shadow_box(img, (60, y + 56, 1020, y + 250), "#1b1b2b", r=18, width=0)
d = ImageDraw.Draw(img)
para(d, 86, y + 74, prompt, font(23, "mono"), "#ffd166", 900, gap=6)
d.text((86, y + 160), f"Context: [1] {hits[0].text[:48]}...", font=font(23, "mono"), fill="#9aa0b4")
d.text((86, y + 198), f"Question: {q}", font=font(23, "mono"), fill="#ffffff")
img.save(OUT / "4_answer.png")

# ------------------------------------------------------------------ 5 failure
img, d = new_card("5 / 6", "Watch it slip (on purpose)", "BM25 matches words, not meaning", CORAL)
q = "Which planet is the warmest?"
hits, ans = ask(small_idx, q)
shadow_box(img, (60, 290, 1020, 700), "white", outline=CORAL, width=4, r=22)
d = ImageDraw.Draw(img)
d.text((90, 310), f'Q: "{q}"', font=font(30, "bold"), fill=INK)
miss = [t for t in tokenize(q) if t not in small_idx._bm25.idf]
d.text((90, 362), f"'{miss[0]}' appears in no document, so it scores 0.", font=font(26), fill=CORAL)
d.text((90, 404), "The document says 'hottest'. Same idea, different word.", font=font(26), fill=SOFT)
d.text((90, 462), "What minirag answered:", font=font(26, "handb"), fill=INK)
para(d, 90, 506, ans, font(26, "mono"), BLUE, 880, gap=6)
emoji(d, (950, 310), "🤔", 56)
hits2 = small_idx.search("kubernetes cluster")
shadow_box(img, (60, 740, 1020, 920), "white", outline=SOFT, width=2, r=22)
d = ImageDraw.Draw(img)
d.text((90, 760), 'Q: "kubernetes cluster"', font=font(30, "bold"), fill=INK)
d.text((90, 812), "-> " + ("no chunks matched, so it says so." if not hits2 else "unexpected hits"), font=font(26, "mono"), fill=TEAL)
d.text((90, 860), "Better to say nothing than to make something up.", font=font(26, "hand"), fill=SOFT)
d.text((60, 970), "Where it goes next", font=font(40, "bold"), fill=INK)
cols = [("Now", TEAL, ["BM25 retrieval", "overlapping chunks", "local Ollama mode"]),
        ("Next", MUSTARD, ["embeddings", "hybrid search", "eval questions"]),
        ("Later", PINK, ["saved index", "inline citations", "web UI"])]
x = 60
for name, col, items in cols:
    shadow_box(img, (x, 1030, x + 300, 1270), col, r=18, width=0)
    d = ImageDraw.Draw(img)
    d.text((x + 22, 1044), name, font=font(32, "handb"), fill=INK)
    for j, it in enumerate(items):
        d.text((x + 22, 1100 + j * 44), "• " + it, font=font(25), fill=INK)
    x += 330
img.save(OUT / "5_limits.png")

# ------------------------------------------------------------------ 6 try it
img, d = new_card("6 / 6", "Try it in 30 seconds", "no accounts, no keys", TEAL)
terminal(img, (60, 290, 1020, 800), [
    ("$ git clone https://github.com/mulisa7/minirag", "#ffffff"),
    ("$ cd minirag && pip install -e .", "#ffffff"), ("", "#ffffff"),
    ("$ minirag index examples/docs", "#ffffff"),
    ("indexed 2 chunks -> .minirag.json", "#9aa0b4"), ("", "#ffffff"),
    ('$ minirag ask "tallest volcano"', "#ffffff"),
    (extractive("tallest volcano", default_idx.search("tallest volcano")), "#06d6a0"),
    ("", "#ffffff"), ("$ minirag ask \"...\" --ollama llama3.2", "#ffd166")])
d = ImageDraw.Draw(img)
d.text((60, 850), "Point it at your own notes", font=font(40, "bold"), fill=INK)
for j, (cmd, note) in enumerate([("minirag index ~/notes", ".txt .md .rst .pdf"),
                                 ("minirag search \"...\" -k 3", "see chunks + scores"),
                                 ("minirag ask \"...\" --ollama MODEL", "local LLM writes the answer")]):
    yy = 930 + j * 90
    shadow_box(img, (60, yy, 1020, yy + 72), "white", outline="#d8d2bb", width=2, r=16)
    d = ImageDraw.Draw(img)
    d.text((86, yy + 18), cmd, font=font(25, "monob"), fill=BLUE)
    d.text((620, yy + 20), note, font=font(24, "hand"), fill=SOFT)
d.text((60, 1220), "Built to learn how RAG works. Questions and PRs welcome.", font=font(30, "handb"), fill=CORAL)
img.save(OUT / "6_try_it.png")
print("wrote", len(list(OUT.glob("*.png"))), "images")
