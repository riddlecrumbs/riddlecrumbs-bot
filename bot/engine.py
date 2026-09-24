"""Riddle Crumbs reel engine. 1080x1920 @30fps, 7s, silent AAC. Frame 0 always shows the hook (cover frame)."""
import math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
ROOT = Path(__file__).resolve().parent.parent
FD = os.environ.get("FONT_DIR", str(ROOT / "fonts")) + "/"
F_BLACK = FD + "inter/extras/ttf/InterDisplay-Black.ttf"
F_XB = FD + "inter/extras/ttf/Inter-ExtraBold.ttf"
F_BOLD = FD + "inter/extras/ttf/Inter-Bold.ttf"
F_SEMI = FD + "inter/extras/ttf/Inter-SemiBold.ttf"
F_MONO = FD + "jb/fonts/ttf/JetBrainsMono-Bold.ttf"

W, H, FPS, DUR = 1080, 1920, 30, 7.0
X0, X1 = 90, 990
BG = (32, 18, 64)
BG2 = (52, 28, 104)
TEXT = (250, 246, 255)
MUTED = (178, 164, 214)
COOKIE = (255, 196, 61)
CARD = (48, 30, 92)
CARD_EDGE = (78, 54, 138)
GOOD = (72, 230, 150)
HANDLE = "@riddlecrumbs"

TAGS = {  # format -> accent colour
    "RIDDLE": COOKIE, "QUIZ": (110, 196, 255), "MATHS TRICK": (255, 128, 190),
    "DID YOU KNOW?": GOOD, "BRAIN TEST": (196, 160, 255), "LIFE HACK": (255, 150, 80),
}

_fc = {}
def font(p, s):
    k = (p, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, int(s))
    return _fc[k]

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def prog(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def pop(t, a, d=0.3):
    """overshoot scale-in 0->1."""
    x = max(0.0, min(1.0, (t - a) / d))
    if x >= 1: return 1.0
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def make_bg():
    bg = Image.new("RGB", (W, H), BG)
    g = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(g)
    d.ellipse([-300, -200, 800, 800], fill=BG2)
    d.ellipse([500, 1100, 1500, 2200], fill=(60, 30, 110))
    bg = Image.blend(bg, g.filter(ImageFilter.GaussianBlur(180)), 0.9)
    # scattered 'crumbs'
    import random
    rnd = random.Random(7)
    d = ImageDraw.Draw(bg)
    for _ in range(70):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(2, 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(70, 50, 118))
    return bg

LOGO = Image.open(ROOT / "assets" / "logo.png").resize((64, 64), Image.LANCZOS)
_m = Image.new("L", (64, 64), 0); ImageDraw.Draw(_m).ellipse([0, 0, 63, 63], fill=255)

def mark(text):
    """-> [(word, highlighted)] ; '*a b*' highlights a phrase, punctuation after '*' allowed."""
    out, on = [], False
    for w in text.split():
        if w.startswith("*"): on = True
        closes = "*" in w.lstrip("*")
        out.append((w.replace("*", ""), on))
        if closes: on = False
    return out

def rich_block(d, text, f, y, color, hi, center=False, lh=1.12, maxw=X1 - X0):
    words = mark(text)
    lines, cur = [], []
    for w in words:
        test = " ".join(x for x, _ in cur + [w])
        if cur and d.textlength(test, font=f) > maxw:
            lines.append(cur); cur = [w]
        else: cur.append(w)
    lines.append(cur)
    sp = d.textlength(" ", font=f)
    for ln in lines:
        total = sum(d.textlength(w, font=f) for w, _ in ln) + sp * (len(ln) - 1)
        x = W / 2 - total / 2 if center else X0
        for w, h in ln:
            d.text((x, y), w, font=f, fill=hi if h else color)
            x += d.textlength(w, font=f) + sp
        y += int(f.size * lh)
    return y

def chrome(im, t, tag):
    d = ImageDraw.Draw(im)
    acc = TAGS[tag]
    f = font(F_XB, 30)
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle([X0, 270, X0 + tw + 44, 324], radius=27, fill=acc)
    d.text((X0 + 22, 280), tag, font=f, fill=BG)
    fh = font(F_SEMI, 30)
    hw = d.textlength(HANDLE, font=fh)
    d.text((X1 - hw, 281), HANDLE, font=fh, fill=MUTED)
    im.paste(LOGO, (int(X1 - hw - 78), 265), _m)
    # progress
    d.rounded_rectangle([X0, 228, X1, 234], radius=3, fill=(64, 44, 112))
    d.rounded_rectangle([X0, 228, X0 + (X1 - X0) * t / DUR, 234], radius=3, fill=acc)
    return d, acc

def fade_paste(im, layer, a):
    if a <= 0: return
    if a < 1: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    im.paste(layer, (0, 0), layer)

def new_layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return L, ImageDraw.Draw(L)

def countdown(im, t, t0, secs, cx, cy, r, acc):
    """ring countdown from secs to 0 starting at t0."""
    if t < t0: return
    d = ImageDraw.Draw(im)
    el = min(secs, t - t0)
    left = max(0, math.ceil(secs - el - 1e-6))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(70, 50, 120), width=14)
    frac = 1 - el / secs
    if frac > 0:
        d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=acc, width=14)
    f = font(F_BLACK, int(r * 0.95))
    s = str(left) if el < secs else "0"
    d.text((cx, cy + 4), s, font=f, fill=TEXT, anchor="mm")

def cta(im, t, t0, text, y, acc):
    a = prog(t, t0, t0 + 0.3)
    if a <= 0: return
    L, ld = new_layer()
    f = font(F_XB, 40)
    tw = ld.textlength(text, font=f)
    s = 0.9 + 0.1 * pop(t, t0, 0.35)
    w, h = (tw + 70) * s, 88 * s
    x = W / 2 - w / 2
    ld.rounded_rectangle([x, y, x + w, y + h], radius=h / 2, fill=acc + (255,))
    ld.text((W / 2, y + h / 2 + 2), text, font=font(F_XB, 40 * s), fill=BG + (255,), anchor="mm")
    fade_paste(im, L, a)

# ---------------- formats ----------------
def f_riddle(im, t, r):
    d, acc = chrome(im, t, "RIDDLE")
    y = r.get("y0", 560) + int(16 * (1 - prog(t, 0, 0.35)))
    y = rich_block(d, r["q"], font(F_BLACK, r.get("size", 96)), y, TEXT, acc)
    y += 70
    countdown(im, t, 1.4, 4, W // 2, y + 150, 140, acc)
    cta(im, t, 5.4, "Comment your answer  ↓", y + 360, acc)
    L, ld = new_layer()
    ld.text((W / 2, y + 500), "Answer in the caption", font=font(F_SEMI, 34), fill=MUTED + (255,), anchor="mm")
    fade_paste(im, L, prog(t, 5.7, 6.0))

def f_quiz(im, t, r):
    d, acc = chrome(im, t, "QUIZ")
    y = r.get("y0", 440) + int(16 * (1 - prog(t, 0, 0.35)))
    y = rich_block(d, r["q"], font(F_BLACK, 84), y, TEXT, acc)
    y += 50
    reveal = 5.2
    fo = font(F_BOLD, 48)
    for i, opt in enumerate(r["opts"]):
        a = prog(t, 0.15 + i * 0.1, 0.4 + i * 0.1)
        if a <= 0: continue
        L, ld = new_layer()
        yy = y + i * 128 + int(30 * (1 - a))
        correct = i == r["ans"]
        rv = prog(t, reveal, reveal + 0.25)
        fill, edge, txt = CARD, CARD_EDGE, TEXT
        if rv > 0 and correct: fill, edge, txt = GOOD, GOOD, BG
        ld.rounded_rectangle([X0, yy, X1, yy + 104], radius=24, fill=fill + (255,), outline=edge + (255,), width=3)
        letter = "ABCD"[i]
        ld.ellipse([X0 + 22, yy + 20, X0 + 86, yy + 84], fill=(acc if not (rv > 0 and correct) else BG) + (255,))
        ld.text((X0 + 54, yy + 53), letter, font=font(F_XB, 36), fill=(BG if not (rv > 0 and correct) else GOOD) + (255,), anchor="mm")
        ld.text((X0 + 116, yy + 52), opt, font=fo, fill=txt + (255,), anchor="lm")
        if rv > 0 and correct:
            ld.text((X1 - 40, yy + 52), "✓", font=font(F_BLACK, 56), fill=BG + (255,), anchor="rm")
        alpha = a * (1 - 0.6 * rv if not correct else 1)
        fade_paste(im, L, alpha)
    yc = y + 4 * 128 + 40
    if t < reveal:
        countdown(im, t, 1.4, 3.8, W // 2, yc + 90, 80, acc)
    else:
        L, ld = new_layer()
        ld.text((W / 2, yc + 40), r["why"], font=font(F_SEMI, 38), fill=TEXT + (255,), anchor="ma")
        fade_paste(im, L, prog(t, reveal + 0.3, reveal + 0.6))
        cta(im, t, reveal + 0.8, "Did you get it?  Comment ↓", yc + 120, acc)

def f_maths(im, t, r):
    """r['steps'] = [[start_time, big_text, label], ...]; last step shown in accent colour."""
    d, acc = chrome(im, t, "MATHS TRICK")
    y = r.get("y0", 540) + int(16 * (1 - prog(t, 0, 0.35)))
    y = rich_block(d, r["q"], font(F_BLACK, 92), y, TEXT, acc)
    y += 90
    steps = r["steps"]
    cur = None
    for i, st in enumerate(steps):
        if t >= st[0]: cur = (i, st)
    if cur:
        i, (ts, s, label) = cur
        L, ld = new_layer()
        size = 170
        while font(F_BLACK, size).getlength(s) > (X1 - X0) - 80 and size > 60: size -= 4
        col = acc if i == len(steps) - 1 else TEXT
        ld.rounded_rectangle([X0, y, X1, y + 300], radius=36, fill=CARD + (255,), outline=CARD_EDGE + (255,), width=3)
        ld.text((W / 2, y + 150), s, font=font(F_BLACK, size), fill=col + (255,), anchor="mm")
        fade_paste(im, L, 1)
        if label:
            L, ld = new_layer()
            ld.text((W / 2, y + 350), label, font=font(F_BOLD, 44), fill=MUTED + (255,), anchor="ma")
            fade_paste(im, L, prog(t, ts, ts + 0.25))
    cta(im, t, 5.6, "Save it. Try it on a friend", y + 470, acc)

def f_fact(im, t, r):
    d, acc = chrome(im, t, "DID YOU KNOW?")
    y = r.get("y0", 520) + int(16 * (1 - prog(t, 0, 0.35)))
    y = rich_block(d, r["q"], font(F_BLACK, 84), y, TEXT, acc)
    y += 20
    # giant stat
    s_ = pop(t, 0.35, 0.45)
    if s_ > 0:
        L, ld = new_layer()
        size = 260
        while font(F_BLACK, size).getlength(r["stat"]) > (X1 - X0) and size > 80: size -= 4
        f = font(F_BLACK, max(1, int(size * s_)))
        ld.text((X0, y + 150), r["stat"], font=f, fill=acc + (255,), anchor="lm")
        fade_paste(im, L, min(1, s_))
    y += 330
    L, ld = new_layer()
    yy = y + int(24 * (1 - prog(t, 2.4, 2.8)))
    end = rich_block(ld, r["more"], font(F_BLACK, 76), yy, TEXT + (255,), acc + (255,))
    end -= int(24 * (1 - prog(t, 2.4, 2.8)))
    fade_paste(im, L, prog(t, 2.4, 2.8))
    cta(im, t, 5.0, "Follow for a daily crumb", end + 50, acc)

def f_stroop(im, t, r):
    d, acc = chrome(im, t, "BRAIN TEST")
    y = r.get("y0", 500) + int(16 * (1 - prog(t, 0, 0.35)))
    y = rich_block(d, "Say the *colour*, not the word.", font(F_BLACK, 92), y, TEXT, acc)
    y += 70
    words = r["words"]  # list of (word, rgb)
    f = font(F_BLACK, 92)
    cols = 2
    for i, (wd, c) in enumerate(words):
        a = prog(t, 0.9 + i * 0.12, 1.2 + i * 0.12)
        if a <= 0: continue
        L, ld = new_layer()
        cx = X0 + (X1 - X0) * (0.25 + 0.5 * (i % cols))
        cy = y + 70 + (i // cols) * 150
        ld.text((cx, cy), wd, font=f, fill=tuple(c) + (255,), anchor="mm")
        fade_paste(im, L, a)
    cta(im, t, 5.3, "Harder than it looks, right?", y + 520, acc)

def keycap(ld, x, y, label, acc, h=120):
    f = font(F_MONO, 50)
    w = max(h, ld.textlength(label, font=f) + 60)
    ld.rounded_rectangle([x, y + 10, x + w, y + h + 10], radius=22, fill=(20, 10, 44, 255))
    ld.rounded_rectangle([x, y, x + w, y + h], radius=22, fill=(250, 246, 255, 255))
    ld.text((x + w / 2, y + h / 2), label, font=f, fill=BG + (255,), anchor="mm")
    return w

def f_hack(im, t, r):
    d, acc = chrome(im, t, "LIFE HACK")
    y = r.get("y0", 520) + int(16 * (1 - prog(t, 0, 0.35)))
    y = rich_block(d, r["q"], font(F_BLACK, 96), y, TEXT, acc)
    y += 90
    for row, rw in enumerate(r["rows"]):
        label, keys = rw[0], rw[1]
        t0 = rw[2] if len(rw) > 2 else 1.2 + 1.4 * row
        a = prog(t, t0, t0 + 0.3)
        if a <= 0: continue
        L, ld = new_layer()
        yy = y + row * 250 + int(24 * (1 - a))
        ld.text((X0, yy), label, font=font(F_BOLD, 40), fill=MUTED + (255,))
        x = X0
        fplus = font(F_BLACK, 60)
        for k, key in enumerate(keys):
            if k:
                ld.text((x + 30, yy + 120), "+", font=fplus, fill=acc + (255,), anchor="mm"); x += 60
            x += keycap(ld, x, yy + 60, key, acc)
        fade_paste(im, L, a)
    cta(im, t, 5.2, r.get("cta", "Send this to someone who needs it"), y + 540, acc)

FORMATS = {"riddle": f_riddle, "quiz": f_quiz, "maths": f_maths, "fact": f_fact, "stroop": f_stroop, "hack": f_hack}

_BG = None
def render(r, out_path, preview_path=None, preview_times=(0.0, 3.0, 6.6)):
    global _BG
    if _BG is None: _BG = make_bg()
    fn = FORMATS[r["type"]]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
           "-shortest", "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "20",
           "-preset", "medium", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k", str(out_path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev, pt = [], [int(x * FPS) for x in preview_times]
    for fi in range(int(DUR * FPS)):
        t = fi / FPS
        im = _BG.copy()
        fn(im, t, r)
        p.stdin.write(im.tobytes())
        if preview_path and fi in pt: prev.append(im.copy())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError("ffmpeg failed")
    if preview_path:
        sheet = Image.new("RGB", (len(prev) * 1100, 1920), "white")
        for i, im in enumerate(prev): sheet.paste(im, (i * 1100, 0))
        sheet.resize((sheet.width // 3, 640)).save(preview_path)
