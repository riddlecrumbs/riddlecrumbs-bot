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


PALETTES = {
    "brand":  [(255, 196, 61), (255, 150, 80), (255, 110, 150), (220, 120, 255), (140, 150, 255), (90, 200, 255), (100, 230, 190)],
    "ocean":  [(40, 120, 255), (60, 180, 255), (80, 230, 240), (120, 255, 210), (200, 255, 240)],
    "sunset": [(255, 80, 90), (255, 130, 70), (255, 190, 80), (255, 230, 140), (255, 160, 200)],
    "neon":   [(255, 40, 160), (190, 60, 255), (80, 120, 255), (40, 230, 255), (120, 255, 140)],
    "candy":  [(255, 170, 210), (255, 210, 150), (200, 255, 190), (170, 220, 255), (220, 190, 255)],
    "aurora": [(70, 255, 170), (60, 220, 230), (120, 140, 255), (190, 110, 255), (255, 120, 220)],
}
PAL_ORDER = ["brand", "ocean", "sunset", "neon", "candy", "aurora"]
PALETTE = PALETTES["brand"]


def grad(u, pal=None):
    """smooth colour ramp through a palette, u in [0,1]."""
    P = PALETTES[pal] if isinstance(pal, str) else (pal or PALETTE)
    u = max(0.0, min(1.0, u)) * (len(P) - 1)
    i = min(int(u), len(P) - 2); f = u - i
    a, b = P[i], P[i + 1]
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


# =============== oddly satisfying ===============
# Each variant is drawn from its own parameters + colour palette, and the queue in content.py
# rotates through every variant and palette, so no two satisfying reels look alike.
LOOPING = {"pendulum", "circle", "orbits", "ripple", "lissajous", "squares", "flower"}


def relax_params(r):
    rnd = random.Random(r["seed"])
    v = r["variant"]
    p = {"pal": r.get("pal", "brand")}
    if v == "pendulum":
        p.update(n=rnd.choice([10, 14, 18]), K=rnd.choice([2, 3, 5]), vertical=rnd.random() < 0.5, size=rnd.choice([18, 24, 30]))
    elif v == "circle":
        p.update(n=rnd.choice([6, 8, 12, 16]), cycles=rnd.choice([1, 2]), ring=rnd.random() < 0.5)
    elif v == "sort":
        n = rnd.choice([24, 36, 48]); hs = list(range(1, n + 1)); rnd.shuffle(hs); p.update(hs=hs, round=rnd.random() < 0.5)
    elif v == "spiro":
        R, rr, dd = rnd.choice([(5, 3, 5), (7, 4, 6), (8, 3, 7), (9, 4, 8), (7, 2, 5), (11, 4, 9), (10, 3, 8), (12, 5, 10)])
        p.update(R=R, r=rr, d=dd, rot=rnd.uniform(0, 6.28), width=rnd.choice([4, 6, 9]))
    elif v == "orbits":
        p.update(n=rnd.choice([5, 6, 7]), base=rnd.choice([1, 2]), dot=rnd.choice([20, 26]))
    elif v == "ripple":
        p.update(cols=rnd.choice([9, 11]), waves=rnd.choice([1, 2]), k=rnd.uniform(0.010, 0.016), shape=rnd.choice(["dot", "square"]))
    elif v == "lissajous":
        a, b = rnd.choice([(3, 2), (5, 4), (3, 4), (5, 6), (4, 5), (7, 6)])
        p.update(a=a, b=b, delta=rnd.choice([math.pi / 2, math.pi / 4]), tail=rnd.choice([0.35, 0.5]))
    elif v == "squares":
        p.update(n=rnd.choice([16, 22, 28]), twist=rnd.uniform(0.18, 0.32), sides=rnd.choice([4, 3, 6]))
    elif v == "flower":
        p.update(petals=rnd.choice([6, 8, 12]), layers=rnd.choice([3, 4, 5]))
    return p


def _hook(im, t, text):
    L, ld = new_layer()
    ld.text((W / 2, 440), text, font=font(E.F_BLACK, 64), fill=TEXT + (255,), anchor="mm")
    fade_paste(im, L, 1.0)


def _poly(cx, cy, r, sides, ang):
    return [(cx + r * math.cos(ang + 2 * math.pi * i / sides), cy + r * math.sin(ang + 2 * math.pi * i / sides)) for i in range(sides)]


@lru_cache(maxsize=8)
def _concept_params(key, seed):
    import loops
    return loops.CONCEPTS[key]["prep"](random.Random(seed))


def f_relax(im, t, r):
    chrome_min(im, "SATISFYING", show_bar=False)
    p = relax_params(r); pal = p["pal"]
    v = r["variant"]
    _hook(im, t, r.get("hook", "Try to look away."))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    import loops
    if v in loops.CONCEPTS:
        loops.CONCEPTS[v]["draw"](d, L, t, _concept_params(v, r["seed"]), lambda u: grad(u, pal))
        glow = L.filter(ImageFilter.GaussianBlur(16))
        im.paste(glow, (0, 0), glow); im.paste(L, (0, 0), L)
        return
    cx, cy = W / 2, 1000
    T = 2 * math.pi * t / DUR
    if v == "pendulum":
        n, K, sz = p["n"], p["K"], p["size"]
        for i in range(n):
            u = i / (n - 1); col = grad(u, pal)
            for g in range(5, -1, -1):  # motion trail
                tg = t - g * 0.018
                s = math.cos(2 * math.pi * (K + i) * tg / DUR)
                if p["vertical"]:
                    x, y = X0 + 40 + (X1 - X0 - 80) * u, cy + 380 * s
                else:
                    x, y = cx + 380 * s, 600 + 840 * u
                rr = sz - g * sz / 10
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (255 if g == 0 else 50,))
    elif v == "circle":
        n, cyc = p["n"], p["cycles"]
        Rad = 380
        a_lines = prog(t, 3.0, 3.6) * (1 - prog(t, 6.2, 6.9))   # reveal the trick, then fade for the loop
        if p["ring"]: d.ellipse([cx - Rad, cy - Rad, cx + Rad, cy + Rad], outline=grad(0.5, pal) + (90,), width=4)
        for k in range(n):
            ang = math.pi * k / n
            dx, dy = math.cos(ang), math.sin(ang)
            if a_lines > 0:
                d.line([(cx - Rad * dx, cy - Rad * dy), (cx + Rad * dx, cy + Rad * dy)], fill=grad(k / n, pal) + (int(120 * a_lines),), width=3)
            s_ = Rad * math.cos(cyc * T - ang)
            x, y = cx + s_ * dx, cy + s_ * dy
            rr = 30 if n <= 8 else 22
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=grad(k / n, pal) + (255,))
        if a_lines > 0:
            d.text((W / 2, 1480), "Each dot only moves in a straight line", font=font(E.F_BOLD, 40),
                   fill=MUTED + (int(255 * a_lines),), anchor="mm")
    elif v == "sort":
        hs = p["hs"]; n = len(hs)
        frames = sort_frames(tuple(hs))
        k = min(len(frames) - 1, int(len(frames) * min(1.0, t / 5.2)))
        arr, active = frames[k]
        sweep = (t - 5.4) / 1.0 if t > 5.4 else -1
        for i, hgt in enumerate(arr):
            col = grad((hgt - 1) / (n - 1), pal)
            if i == active and t < 5.2: col = (255, 255, 255)
            if 0 <= sweep and i <= sweep * n: col = tuple(min(255, c + 60) for c in col)
            if p["round"]:   # radial bars around a circle
                ang = -math.pi / 2 + 2 * math.pi * i / n
                r0, r1 = 120, 120 + 300 * hgt / n
                w = max(4, int(2 * math.pi * 120 / n * 0.7))
                d.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang)), (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))], fill=col + (255,), width=w)
            else:
                bw = (X1 - X0) / n; x0 = X0 + i * bw; h = 792 * hgt / n
                d.rounded_rectangle([x0 + 2, 1440 - h, x0 + bw - 2, 1440], radius=5, fill=col + (255,))
    elif v == "spiro":
        R, rr, dd, rot = p["R"], p["r"], p["d"], p["rot"]
        scale = 380 / (R - rr + dd)
        total = 2 * math.pi * rr / math.gcd(R, rr)
        u_end = total * min(1.0, t / 6.0)
        steps = 1100
        ca, sa = math.cos(rot), math.sin(rot)
        pts = []
        for j in range(steps + 1):
            u = u_end * j / steps
            x = (R - rr) * math.cos(u) + dd * math.cos((R - rr) / rr * u)
            y = (R - rr) * math.sin(u) - dd * math.sin((R - rr) / rr * u)
            pts.append((cx + scale * (x * ca - y * sa), cy + scale * (x * sa + y * ca)))
        fade = 1 - prog(t, 6.3, 6.95)
        for j in range(1, len(pts)):
            d.line([pts[j - 1], pts[j]], fill=grad(j / steps, pal) + (int(255 * fade),), width=p["width"])
        if t < 6.0:
            x, y = pts[-1]; d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(255, 255, 255, 255))
    elif v == "orbits":
        n, base = p["n"], p["base"]
        d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=grad(0, pal) + (255,))
        for i in range(n):
            rad = 90 + 300 * (i + 1) / n
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=grad((i + 1) / n, pal) + (60,), width=2)
            w = (base + n - i) * T               # inner planets lap faster; all realign every loop
            for g in range(14, -1, -1):
                ang = w - g * 0.045 - math.pi / 2
                x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
                rr = p["dot"] * (1 - g / 18)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=grad((i + 1) / n, pal) + (255 if g == 0 else 40,))
    elif v == "ripple":
        cols = p["cols"]
        sp = (X1 - X0) / (cols - 1)
        rows = int(880 / sp) + 1          # keep the grid between the hook text and Instagram's caption area
        gy0 = cy - sp * (rows - 1) / 2
        for i in range(cols):
            for j in range(rows):
                x, y = X0 + i * sp, gy0 + j * sp
                dist = math.hypot(x - cx, y - cy)
                s_ = 0.5 + 0.5 * math.sin(p["waves"] * T * 2 - dist * p["k"])
                rr = 6 + 26 * s_
                col = grad(s_, pal)
                if p["shape"] == "dot": d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (int(110 + 145 * s_),))
                else: d.rounded_rectangle([x - rr, y - rr, x + rr, y + rr], radius=int(rr * 0.3), fill=col + (int(110 + 145 * s_),))
    elif v == "lissajous":
        a, b, de = p["a"], p["b"], p["delta"]
        A = 400
        steps = 260
        for j in range(steps, -1, -1):
            ph = T - p["tail"] * 2 * math.pi * j / steps
            x, y = cx + A * math.sin(a * ph + de), cy + A * math.sin(b * ph)
            fade = 1 - j / steps
            rr = 6 + 16 * fade
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=grad(fade, pal) + (int(255 * fade ** 1.5),))
    elif v == "squares":
        n, tw, sides = p["n"], p["twist"], p["sides"]
        for i in range(n, 0, -1):
            rad = 30 + 420 * i / n
            ang = math.sin(T - i * tw) * math.pi / sides * 1.6 - math.pi / 2
            d.polygon(_poly(cx, cy, rad, sides, ang), outline=grad(i / n, pal) + (255,), width=6)
    elif v == "flower":
        P, Ly = p["petals"], p["layers"]
        for l in range(Ly, 0, -1):
            breathe = 0.75 + 0.25 * math.sin(T - l * 0.6)
            rad = (110 + 300 * l / Ly) * breathe
            rot = (T if l % 2 else -T) / P + l * 0.3
            col = grad(l / Ly, pal)
            for k in range(P):
                ang = rot + 2 * math.pi * k / P
                px, py = cx + rad * 0.55 * math.cos(ang), cy + rad * 0.55 * math.sin(ang)
                pr = rad * 0.42
                d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=col + (230,), width=5)
        d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=grad(0, pal) + (255,))
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
    import loops
    if r["variant"] in loops.CONCEPTS:
        return loops.CONCEPTS[r["variant"]]["events"](_concept_params(r["variant"], r["seed"]))
    p = relax_params(r); v = r["variant"]; ev = []
    penta = [0, 2, 4, 7, 9]
    def note(i, base=72): return base + 12 * (i // 5) + penta[i % 5]
    if v == "pendulum":
        n, K = p["n"], p["K"]
        step = 2 if n <= 14 else 3   # only some balls chime, so it shimmers without getting busy
        for i in range(0, n, step):
            f = (K + i) / DUR
            k = 0
            while k / f < DUR - 1e-6:
                ev.append((k / f, note(n - 1 - i, 67), 0.06)); k += 1
    elif v == "circle":
        n, cyc = p["n"], p["cycles"]
        for k in range(0, n, 1 if n <= 8 else 2):
            ang = math.pi * k / n
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
        for i in range(0, n, max(1, n // 36)):
            ev.append((5.4 + i / n, 64 + int(24 * i / (n - 1)), 0.06))
    elif v == "spiro":
        for j in range(24):
            ev.append((j * 6.0 / 24, note(j % 10, 69), 0.05))
    elif v == "orbits":
        n, base = p["n"], p["base"]
        for i in range(n):
            laps = base + n - i
            for m in range(laps):
                ev.append((m * DUR / laps, note(n - 1 - i, 67), 0.06))   # chime as each planet passes the top
    elif v == "ripple":
        beats = 8 * p["waves"]
        for m in range(beats): ev.append((m * DUR / beats, note(m % 5, 72), 0.05))
    elif v == "lissajous":
        for m in range(14): ev.append((m * DUR / 14, note([0, 2, 4, 2, 1, 3][m % 6], 69), 0.05))
    elif v == "squares":
        for m in range(8): ev.append((m * DUR / 8, note([0, 4, 2, 5][m % 4], 67), 0.06))
    elif v == "flower":
        for m in range(7): ev.append((m * DUR / 7, note([0, 2, 4, 7, 4, 2, 1][m], 69), 0.06))
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


# =============== brain tests (each posted once) ===============
E.TAGS.update({"BRAIN TEST": (196, 160, 255)})


def f_test(im, t, r):
    d, acc = chrome_min(im, "BRAIN TEST", True, t)
    L, ld = new_layer()
    rich_block(ld, r["q"], font(E.F_BLACK, 80), 400, TEXT + (255,), acc + (255,))
    fade_paste(im, L, 1.0)
    reveal = 4.6
    rv = prog(t, reveal, reveal + 0.4)
    k = r["kind"]
    L, ld = new_layer()
    if k in ("countf", "scramble"):
        f = font(E.F_BLACK if k == "countf" else E.F_BOLD, 60 if k == "countf" else 58)
        words = r["text"].split(); rows, cur = [], []
        for w in words:
            if cur and ld.textlength(" ".join(cur + [w]), font=f) > X1 - X0 - 60: rows.append(cur); cur = [w]
            else: cur.append(w)
        rows.append(cur)
        y = 640
        ld.rounded_rectangle([X0, y - 40, X1, y + len(rows) * 84 + 30], radius=32, fill=CARD + (255,), outline=E.CARD_EDGE + (255,), width=3)
        for row in rows:
            line = " ".join(row); x = (W - ld.textlength(line, font=f)) / 2
            for ch in line:
                col = TEXT
                if k == "countf" and ch == "F" and rv > 0: col = tuple(int(lerp_c(TEXT[i], acc[i], rv)) for i in range(3))
                ld.text((x, y), ch, font=f, fill=col + (255,)); x += ld.textlength(ch, font=f)
            y += 84
        end = y + 60
    elif k == "thethe":
        # classic triangle sign with a hidden repeated word
        tri = [(W / 2, 640), (X1 - 40, 1240), (X0 + 40, 1240)]
        ld.polygon(tri, fill=(250, 246, 255, 255))
        ld.polygon([(W / 2, 700), (X1 - 120, 1200), (X0 + 120, 1200)], fill=(40, 24, 80, 255))
        f = font(E.F_BLACK, 70)
        lines = ["PARIS", "IN THE", "THE SPRING"]
        for i, ln in enumerate(lines):
            ld.text((W / 2, 900 + i * 90), ln, font=f, fill=(250, 246, 255, 255), anchor="mm")
        if rv > 0:
            for i in (1, 2):
                ln = lines[i]; w_all = ld.textlength(ln, font=f); x0 = W / 2 - w_all / 2
                if i == 2: xs, xe = x0, x0 + ld.textlength("THE", font=f)
                else: xs, xe = x0 + ld.textlength("IN ", font=f), x0 + w_all
                yy = 900 + i * 90
                ld.rounded_rectangle([xs - 10, yy - 42, xe + 10, yy + 42], radius=14, outline=acc + (int(255 * rv),), width=7)
        end = 1290
    elif k == "lines":
        L1y, L2y, x0, x1 = 820, 1120, 260, 820
        for y, outward in ((L1y, True), (L2y, False)):
            ld.line([(x0, y), (x1, y)], fill=TEXT + (255,), width=12)
            for x, dirn in ((x0, -1), (x1, 1)):
                s_ = 70 * (dirn if outward else -dirn)
                ld.line([(x, y), (x + s_, y - 60)], fill=TEXT + (255,), width=12)
                ld.line([(x, y), (x + s_, y + 60)], fill=TEXT + (255,), width=12)
        if rv > 0:
            for x in (x0, x1):
                ld.line([(x, 700), (x, 1240)], fill=acc + (int(230 * rv),), width=5)
        end = 1270
    elif k == "circles":
        orange = (255, 150, 60)
        for cx, small in ((330, True), (760, False)):
            cy = 960
            ld.ellipse([cx - 62, cy - 62, cx + 62, cy + 62], fill=orange + (255,))
            n, ring, rr = (8, 110, 26) if small else (6, 215, 92)
            for kk in range(n):
                a = 2 * math.pi * kk / n
                x, y = cx + ring * math.cos(a), cy + ring * math.sin(a)
                ld.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(140, 150, 255, 255))
        if rv > 0:
            for cx in (330, 760):
                ld.ellipse([cx - 62, 960 - 62, cx + 62, 960 + 62], outline=(255, 255, 255, int(255 * rv)), width=6)
            ld.line([(330, 960 + 62), (760, 960 + 62)], fill=acc + (int(220 * rv),), width=4)
            ld.line([(330, 960 - 62), (760, 960 - 62)], fill=acc + (int(220 * rv),), width=4)
        end = 1290
    fade_paste(im, L, prog(t, 0.1, 0.4))
    if t < reveal:
        E.countdown(im, t, 1.0, reveal - 1.0, W // 2, end + 110, 70, acc)
    else:
        L, ld = new_layer()
        ld.text((W / 2, end + 70), r["answer"], font=font(E.F_BLACK, 48), fill=acc + (255,), anchor="mm")
        fade_paste(im, L, rv)
        cta(im, t, reveal + 0.9, "Did it get you?  Comment ↓", end + 140, acc)


def lerp_c(a, b, u): return a + (b - a) * u


E.FORMATS.update({"test": f_test})
