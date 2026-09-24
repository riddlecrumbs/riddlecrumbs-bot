"""Zero-effort formats: oddly satisfying loops, would-you-rather, and birth-month games.
Registers itself into engine.FORMATS on import."""
import math, os, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import engine as E
from engine import W, H, DUR, X0, X1, BG, TEXT, MUTED, CARD, CARD_EDGE, font, prog, pop, new_layer, fade_paste, cta, rich_block

_local_emoji = os.path.join(E.FD, "NotoColorEmoji.ttf")
EMOJI_FONT = os.environ.get("EMOJI_FONT") or (_local_emoji if os.path.exists(_local_emoji)
                                              else "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
E.TAGS.update({"SATISFYING": (120, 226, 214), "WOULD YOU RATHER": (255, 128, 190), "BIRTH MONTH": (255, 196, 61)})


@lru_cache(maxsize=256)
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    bb = im.getbbox() or (0, 0, 160, 160)
    im = im.crop(bb)
    s = size / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def paste_emoji(layer, ch, cx, cy, size, alpha=1.0):
    e = emoji(ch, int(size))
    if alpha < 1:
        e = e.copy(); e.putalpha(e.getchannel("A").point(lambda v: int(v * alpha)))
    layer.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))


def chrome_min(im, tag, show_bar=True, t=0.0):
    d = ImageDraw.Draw(im)
    acc = E.TAGS[tag]
    f = font(E.F_XB, 30)
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle([X0, 270, X0 + tw + 44, 324], radius=27, fill=acc)
    d.text((X0 + 22, 280), tag, font=f, fill=BG)
    fh = font(E.F_SEMI, 30)
    hw = d.textlength(E.HANDLE, font=fh)
    d.text((X1 - hw, 281), E.HANDLE, font=fh, fill=MUTED)
    im.paste(E.LOGO, (int(X1 - hw - 78), 265), E._m)
    if show_bar:
        d.rounded_rectangle([X0, 228, X1, 234], radius=3, fill=(64, 44, 112))
        d.rounded_rectangle([X0, 228, X0 + (X1 - X0) * t / DUR, 234], radius=3, fill=acc)
    return d, acc


PALETTE = [(255, 196, 61), (255, 150, 80), (255, 110, 150), (220, 120, 255), (140, 150, 255), (90, 200, 255), (100, 230, 190)]


def grad(u):
    """smooth colour ramp through the brand palette, u in [0,1]."""
    u = max(0.0, min(1.0, u)) * (len(PALETTE) - 1)
    i = min(int(u), len(PALETTE) - 2); f = u - i
    a, b = PALETTE[i], PALETTE[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


# =============== oddly satisfying ===============
# Every variant is periodic in DUR, so the reel loops seamlessly on Instagram.
def relax_params(r):
    rnd = random.Random(r["seed"])
    v = r["variant"]
    if v == "pendulum": return {"n": rnd.choice([12, 14]), "K": rnd.choice([3, 4])}
    if v == "circle": return {"n": rnd.choice([8, 10, 12]), "cycles": 2}
    if v == "sort":
        n = 36; hs = list(range(1, n + 1)); rnd.shuffle(hs); return {"hs": hs}
    if v == "spiro":
        R, rr, dd = rnd.choice([(5, 3, 5), (7, 4, 6), (8, 3, 7), (9, 4, 8), (7, 2, 5)])
        return {"R": R, "r": rr, "d": dd, "rot": rnd.uniform(0, 6.28)}
    return {}


def _hook(im, t, text):
    L, ld = new_layer()
    ld.text((W / 2, 440), text, font=font(E.F_BLACK, 64), fill=TEXT + (255,), anchor="mm")
    fade_paste(im, L, 1.0)


def f_relax(im, t, r):
    chrome_min(im, "SATISFYING", show_bar=False)
    p = relax_params(r)
    v = r["variant"]
    _hook(im, t, r.get("hook", "Try to look away."))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    cx, cy = W / 2, 1000
    if v == "pendulum":
        n, K = p["n"], p["K"]
        top, bot = 600, 1440
        A = 380
        for i in range(n):
            y = top + (bot - top) * i / (n - 1)
            col = grad(i / (n - 1))
            d.line([(cx - A, y), (cx + A, y)], fill=col + (40,), width=2)
            for g in range(5, -1, -1):  # motion trail
                tg = t - g * 0.018
                x = cx + A * math.cos(2 * math.pi * (K + i) * tg / DUR)
                rr = 26 - g * 2.5
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (255 if g == 0 else 50,))
    elif v == "circle":
        n, cyc = p["n"], p["cycles"]
        Rad = 380
        a_lines = prog(t, 3.0, 3.6) * (1 - prog(t, 6.2, 6.9))   # lines reveal the trick, then fade for the loop
        d.ellipse([cx - Rad, cy - Rad, cx + Rad, cy + Rad], outline=(90, 70, 150, 255), width=4)
        for k in range(n):
            ang = math.pi * k / n
            dx, dy = math.cos(ang), math.sin(ang)
            if a_lines > 0:
                d.line([(cx - Rad * dx, cy - Rad * dy), (cx + Rad * dx, cy + Rad * dy)], fill=grad(k / n) + (int(120 * a_lines),), width=3)
            s = Rad * math.cos(2 * math.pi * cyc * t / DUR - ang)
            x, y = cx + s * dx, cy + s * dy
            d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=grad(k / n) + (255,))
        if a_lines > 0:
            d.text((W / 2, 1480), "Each dot only moves in a straight line", font=font(E.F_BOLD, 40),
                   fill=MUTED + (int(255 * a_lines),), anchor="mm")
    elif v == "sort":
        hs = p["hs"]; n = len(hs)
        frames = sort_frames(tuple(hs))
        k = min(len(frames) - 1, int(len(frames) * min(1.0, t / 5.2)))
        arr, active = frames[k]
        bw = (X1 - X0) / n
        base = 1440
        sweep = (t - 5.4) / 1.0 if t > 5.4 else -1
        for i, hgt in enumerate(arr):
            x0 = X0 + i * bw
            h = 22 * hgt
            col = grad((hgt - 1) / (n - 1))
            if i == active and t < 5.2: col = (255, 255, 255)
            if 0 <= sweep and i <= sweep * n: col = tuple(min(255, c + 60) for c in col)
            d.rounded_rectangle([x0 + 3, base - h, x0 + bw - 3, base], radius=6, fill=col + (255,))
    elif v == "spiro":
        R, rr, dd, rot = p["R"], p["r"], p["d"], p["rot"]
        scale = 380 / (R - rr + dd)
        total = 2 * math.pi * rr / math.gcd(R, rr)
        u_end = total * min(1.0, t / 6.0)
        steps = 900
        pts = []
        for j in range(steps + 1):
            u = u_end * j / steps
            x = (R - rr) * math.cos(u) + dd * math.cos((R - rr) / rr * u)
            y = (R - rr) * math.sin(u) - dd * math.sin((R - rr) / rr * u)
            ca, sa = math.cos(rot), math.sin(rot)
            pts.append((cx + scale * (x * ca - y * sa), cy + scale * (x * sa + y * ca)))
        fade = 1 - prog(t, 6.3, 6.95)
        for j in range(1, len(pts)):
            d.line([pts[j - 1], pts[j]], fill=grad(j / steps) + (int(255 * fade),), width=6)
        if t < 6.0:
            x, y = pts[-1]; d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(255, 255, 255, 255))
    glow = L.filter(ImageFilter.GaussianBlur(18))
    im.paste(glow, (0, 0), glow)
    im.paste(L, (0, 0), L)


@lru_cache(maxsize=16)
def sort_frames(hs):
    """insertion sort, recording (array, active index) after each shift."""
    a = list(hs); out = [(tuple(a), -1)]
    for i in range(1, len(a)):
        j = i
        while j > 0 and a[j - 1] > a[j]:
            a[j - 1], a[j] = a[j], a[j - 1]; j -= 1
            out.append((tuple(a), j))
    out.append((tuple(a), -1))
    return out


def relax_events(r):
    """(time, midi_note, gain) plucks that match the motion."""
    p = relax_params(r); v = r["variant"]; ev = []
    penta = [0, 2, 4, 7, 9]
    def note(i, base=72): return base + 12 * (i // 5) + penta[i % 5]
    if v == "pendulum":
        n, K = p["n"], p["K"]
        for i in range(0, n, 2):   # every other ball chimes, so it shimmers without getting busy
            f = (K + i) / DUR
            k = 0
            while k / f < DUR - 1e-6:
                ev.append((k / f, note(n - 1 - i, 67), 0.06)); k += 1
    elif v == "circle":
        n, cyc = p["n"], p["cycles"]
        for k in range(n):
            ang = math.pi * k / n
            # dot passes the centre when cos(...) = 0
            for m in range(4 * cyc):
                tt = (ang + math.pi / 2 + m * math.pi) * DUR / (2 * math.pi * cyc)
                if 0 <= tt < DUR: ev.append((tt, note(k, 72), 0.07))
    elif v == "sort":
        frames = sort_frames(tuple(p["hs"])); n = len(p["hs"])
        last = -1
        for fi in range(int(5.2 * 30)):
            t = fi / 30
            k = min(len(frames) - 1, int(len(frames) * t / 5.2))
            arr, act = frames[k]
            if act >= 0 and k != last:
                ev.append((t, 60 + int(24 * (arr[act] - 1) / (n - 1)), 0.04)); last = k
        for i in range(n):
            ev.append((5.4 + i / n, 64 + int(24 * i / (n - 1)), 0.06))
    elif v == "spiro":
        for j in range(24):
            ev.append((j * 6.0 / 24, note(j % 10, 69), 0.05))
    return ev


# =============== would you rather ===============
def f_wyr(im, t, r):
    d, acc = chrome_min(im, "WOULD YOU RATHER", True, t)
    L, ld = new_layer()
    rich_block(ld, "Would you *rather...*", font(E.F_BLACK, 84), 400, TEXT + (255,), acc + (255,))
    fade_paste(im, L, 1.0)
    cards = [("A", r["a"], r["ea"], (255, 128, 190), 560, 0.15), ("B", r["b"], r["eb"], (110, 196, 255), 1060, 1.1)]
    for letter, text, em, col, y, t0 in cards:
        a = prog(t, t0, t0 + 0.4)
        if a <= 0: continue
        L, ld = new_layer()
        off = int((1 - a) * (-260 if letter == "A" else 260))
        x0, x1, y1 = X0 + off, X1 + off, y + 400
        ld.rounded_rectangle([x0, y, x1, y1], radius=40, fill=CARD + (255,), outline=col + (255,), width=5)
        ld.ellipse([x0 + 30, y + 30, x0 + 110, y + 110], fill=col + (255,))
        ld.text((x0 + 70, y + 72), letter, font=font(E.F_BLACK, 50), fill=BG + (255,), anchor="mm")
        paste_emoji(L, em, (x0 + x1) / 2, y + 150, 170)
        f = font(E.F_BLACK, 58)
        lines = E.mark(text)
        # centred wrapped text under the emoji
        words = [w for w, _ in lines]; rows, cur = [], []
        for w in words:
            if cur and ld.textlength(" ".join(cur + [w]), font=f) > (X1 - X0) - 100: rows.append(cur); cur = [w]
            else: cur.append(w)
        rows.append(cur)
        ty = y + 265 - (len(rows) - 1) * 34
        for row in rows:
            ld.text(((x0 + x1) / 2, ty), " ".join(row), font=f, fill=TEXT + (255,), anchor="mm"); ty += 66
        fade_paste(im, L, a)
    s = pop(t, 0.8, 0.4)
    if s > 0:
        L, ld = new_layer()
        rr = 70 * s
        ld.ellipse([W / 2 - rr, 1010 - rr, W / 2 + rr, 1010 + rr], fill=TEXT + (255,))
        ld.text((W / 2, 1012), "OR", font=font(E.F_BLACK, max(1, int(48 * s))), fill=BG + (255,), anchor="mm")
        fade_paste(im, L, min(1, s))
    cta(im, t, 3.2, "Comment A or B  ↓", 1485, acc)


# =============== birth month ===============
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def f_month(im, t, r):
    d, acc = chrome_min(im, "BIRTH MONTH", True, t)
    L, ld = new_layer()
    rich_block(ld, f"Your birth month = your *{r['what']}*", font(E.F_BLACK, 72), 370, TEXT + (255,), acc + (255,))
    fade_paste(im, L, 1.0)
    cw, ch, gx, gy = 280, 196, 30, 20
    top = 560
    for i, (em, label) in enumerate(r["items"]):
        a = prog(t, 0.25 + i * 0.16, 0.5 + i * 0.16)
        if a <= 0: continue
        col, row = i % 3, i // 3
        x = X0 + col * (cw + gx); y = top + row * (ch + gy) + int(20 * (1 - a))
        L, ld = new_layer()
        ld.rounded_rectangle([x, y, x + cw, y + ch], radius=26, fill=CARD + (255,), outline=CARD_EDGE + (255,), width=3)
        ld.text((x + 20, y + 16), MONTHS[i], font=font(E.F_XB, 28), fill=acc + (255,))
        paste_emoji(L, em, x + cw / 2, y + 88, 78)
        f = font(E.F_BOLD, 32)
        while ld.textlength(label, font=f) > cw - 24 and f.size > 20: f = font(E.F_BOLD, f.size - 2)
        ld.text((x + cw / 2, y + 160), label, font=f, fill=TEXT + (255,), anchor="mm")
        fade_paste(im, L, a)
    cta(im, t, 2.8, "Comment yours  ↓", 1450, acc)


E.FORMATS.update({"relax": f_relax, "wyr": f_wyr, "month": f_month})
