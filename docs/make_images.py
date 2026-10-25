"""Draws the explainer cards in docs/images. Needs pillow: pip install pillow"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "images"
OUT.mkdir(exist_ok=True)

W = H = 1080
BG, INK, MUTED = "#0f1720", "#f2f5f8", "#8fa0b3"
ACCENT, ACCENT2, BOX = "#4cc9a7", "#f4b860", "#1b2735"
FONTS = "C:/Windows/Fonts/"


def font(size, bold=False, mono=False):
    name = "consolab.ttf" if mono and bold else "consola.ttf" if mono else "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(FONTS + name, size)


def card(step, title, subtitle=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, H], fill=ACCENT)
    d.text((70, 60), step, font=font(28, True), fill=ACCENT)
    d.text((70, 110), title, font=font(60, True), fill=INK)
    if subtitle:
        d.text((70, 195), subtitle, font=font(30), fill=MUTED)
    d.text((70, H - 70), "minirag", font=font(26, True), fill=MUTED)
    return img, d


def box(d, x, y, w, h, text, sub=None, fill=BOX, edge=ACCENT):
    d.rounded_rectangle([x, y, x + w, y + h], 18, fill=fill, outline=edge, width=3)
    f = font(34, True)
    tw = d.textlength(text, font=f)
    d.text((x + (w - tw) / 2, y + (h / 2 - 30 if sub else h / 2 - 22)), text, font=f, fill=INK)
    if sub:
        sf = font(24)
        sw = d.textlength(sub, font=sf)
        d.text((x + (w - sw) / 2, y + h / 2 + 10), sub, font=sf, fill=MUTED)


def arrow_down(d, x, y1, y2):
    d.line([x, y1, x, y2 - 10], fill=MUTED, width=4)
    d.polygon([(x - 12, y2 - 14), (x + 12, y2 - 14), (x, y2)], fill=MUTED)


def wrap(d, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=f) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def para(d, x, y, text, f, fill, width, gap=10):
    for line in wrap(d, text, f, width):
        d.text((x, y), line, font=f, fill=fill)
        y += f.size + gap
    return y


# 1 ---------------------------------------------------------------- overview
img, d = card("1 / 5", "Ask your own documents", "A small RAG tool in plain Python. No API keys.")
y = 290
for text, sub in [("Your files", ".txt  .md  .rst  .pdf"), ("minirag index", "split into chunks, build index"),
                  ("minirag ask", "find the best chunks, answer")]:
    box(d, 190, y, 700, 120, text, sub)
    y += 120
    if text != "minirag ask":
        arrow_down(d, 540, y + 5, y + 60)
        y += 65
para(d, 70, 900, "RAG = retrieve the relevant text first, then answer from it. That is what LlamaIndex and RAGFlow do at a much larger scale.", font(28), MUTED, 940)
img.save(OUT / "1_overview.png")

# 2 ---------------------------------------------------------------- chunking
img, d = card("2 / 5", "Step 1: split into chunks", "Whole sentences, about 120 words, 1 sentence of overlap")
sents = ["Sentence A.", "Sentence B.", "Sentence C.", "Sentence D.", "Sentence E."]
x0, y0 = 90, 330
for i, s in enumerate(sents):
    d.rounded_rectangle([x0 + i * 180, y0, x0 + i * 180 + 165, y0 + 70], 12, fill=BOX, outline=MUTED, width=2)
    d.text((x0 + i * 180 + 14, y0 + 18), s, font=font(24), fill=INK)
d.text((x0, y0 + 95), "The text, cut at sentence ends", font=font(24), fill=MUTED)
box(d, 90, 560, 520, 90, "Chunk 1:  A  B  C", edge=ACCENT)
box(d, 400, 690, 520, 90, "Chunk 2:  C  D  E", edge=ACCENT2)
d.text((620, 585), "<- C is repeated", font=font(26, True), fill=ACCENT2)
para(d, 70, 830, "Why overlap? If an answer sits across a boundary, one chunk still holds the whole thought. Why sentences? Cutting mid-sentence ruins both search and answers.", font(28), MUTED, 940)
img.save(OUT / "2_chunking.png")

# 3 ---------------------------------------------------------------- bm25
img, d = card("3 / 5", "Step 2: rank with BM25", "Keyword scoring, written from scratch in ~30 lines")
rows = [("Rare words count more", "'volcano' beats 'planet': fewer chunks contain it (the IDF part)"),
        ("Repeats help, with a limit", "10 mentions are not 10x better than 1 (saturation, k1 = 1.5)"),
        ("Long chunks are not favoured", "Scores are adjusted for chunk length (b = 0.75)")]
y = 300
for head, body in rows:
    d.rounded_rectangle([70, y, 1010, y + 170], 18, fill=BOX)
    d.text((100, y + 20), head, font=font(36, True), fill=ACCENT)
    para(d, 100, y + 72, body, font(28), INK, 880)
    y += 195
d.text((70, 900), "Sum these over each word in your question. Highest total wins.", font=font(28), fill=MUTED)
img.save(OUT / "3_bm25.png")

# 4 ---------------------------------------------------------------- answer
img, d = card("4 / 5", "Step 3: write the answer", "From the top chunks, in one of two modes")
d.rounded_rectangle([70, 290, 1010, 520], 18, fill=BOX, outline=ACCENT, width=3)
d.text((100, 310), "Default: extractive", font=font(36, True), fill=ACCENT)
para(d, 100, 365, "No model. Pick the sentences from the top chunks that share the most words with the question.", font(28), INK, 880)
d.rounded_rectangle([70, 550, 1010, 780], 18, fill=BOX, outline=ACCENT2, width=3)
d.text((100, 570), "--ollama llama3.2: generated", font=font(36, True), fill=ACCENT2)
para(d, 100, 625, "Send the top chunks to a local model with the rule: answer only from this context and cite sources.", font(28), INK, 880)
d.text((70, 830), "$ minirag ask \"Which planet is the hottest?\"", font=font(28, mono=True), fill=INK)
d.text((70, 880), "Venus is the hottest planet because its thick", font=font(26, mono=True), fill=ACCENT)
d.text((70, 920), "atmosphere traps heat...", font=font(26, mono=True), fill=ACCENT)
img.save(OUT / "4_answer.png")

# 5 ---------------------------------------------------------------- limits
img, d = card("5 / 5", "What it can't do yet", "Honest limits, and the next step")
items = [("Matches words, not meaning", "'automobile' will not find 'car'"),
         ("Index lives in memory", "Fine for thousands of chunks, not millions"),
         ("Extractive answers are rough", "That is why the Ollama mode exists")]
y = 290
for head, body in items:
    d.rounded_rectangle([70, y, 1010, y + 150], 18, fill=BOX)
    d.text((100, y + 22), head, font=font(36, True), fill=INK)
    d.text((100, y + 80), body, font=font(28), fill=MUTED)
    y += 175
d.rounded_rectangle([70, 830, 1010, 960], 18, fill=BOX, outline=ACCENT, width=3)
d.text((100, 850), "Next: embeddings + BM25 hybrid search", font=font(34, True), fill=ACCENT)
d.text((100, 905), "github.com/mulisa7/minirag", font=font(28), fill=MUTED)
img.save(OUT / "5_limits.png")
print("wrote", len(list(OUT.glob("*.png"))), "images")
