"""Library of 'oddly satisfying' concepts. Every concept is a different idea, and the robot posts each one
only once - nothing is ever re-posted with just new colours.

Each concept: draw(d, L, t, P) draws onto the RGBA layer L (ImageDraw d) at time t with prepared params P;
events(P) returns [(time, midi_note, gain)] for sound; prep(rnd) builds params once per reel.
Content area: x 90..990, y ~560..1480, centre (540, 1000).
"""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, DUR = 1080, 1920, 7.0
X0, X1 = 90, 990
CX, CY = 540, 1000
TAU = 2 * math.pi
PENTA = [0, 2, 4, 7, 9]


def note(i, base=72): return base + 12 * (i // 5) + PENTA[i % 5]


def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def lerp(a, b, u): return a + (b - a) * u


CONCEPTS = {}


def concept(key, hook, pal):
    def deco(cls):
        CONCEPTS[key] = {"draw": cls.draw, "events": cls.events, "prep": cls.prep, "hook": hook, "pal": pal}
        return cls
    return deco


# ---------------------------------------------------------------- Newton's cradle
@concept("newton", "That click though...", "brand")
class Newton:
    @staticmethod
    def prep(rnd): return {"swings": 3, "A": 0.5}

    @staticmethod
    def phase(P, t):
        return P["A"] * math.sin(TAU * P["swings"] * t / DUR)

    @staticmethod
    def draw(d, L, t, P, grad):
        bar_y, length, r = 700, 480, 54
        d.rounded_rectangle([CX - 360, bar_y - 18, CX + 360, bar_y + 6], radius=10, fill=(200, 190, 230, 255))
        th = Newton.phase(P, t)
        for i in range(5):
            px = CX + (i - 2) * 2 * r
            ang = th if (i == 0 and th < 0) or (i == 4 and th > 0) else 0.0
            bx, by = px + length * math.sin(ang), bar_y + length * math.cos(ang)
            for side in (-1, 1):
                d.line([(px + side * 40, bar_y), (bx, by)], fill=(180, 170, 220, 160), width=3)
            col = grad(i / 4)
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=col + (255,))
            d.ellipse([bx - r * 0.55, by - r * 0.6, bx - r * 0.05, by - r * 0.15], fill=(255, 255, 255, 120))

    @staticmethod
    def events(P):
        # clack each time the swinging ball comes back to rest against the others
        return [(k * DUR / (2 * P["swings"]), 84, 0.18) for k in range(2 * P["swings"])] + \
               [(k * DUR / (2 * P["swings"]) + 0.01, 96, 0.08) for k in range(2 * P["swings"])]


# ---------------------------------------------------------------- Meshing gears
@concept("gears", "Perfectly in sync.", "sunset")
class Gears:
    @staticmethod
    def prep(rnd):
        # (teeth, radius) - pitch matched so they mesh
        return {"g": [(24, 230, CX - 120, 860), (12, 115, CX + 225, 860 + 0), (16, 153, CX + 60, 1225)], "shift": 6}

    @staticmethod
    def gear(d, cx, cy, teeth, R, ang, col):
        pts = []
        for k in range(teeth * 4):
            a = ang + TAU * k / (teeth * 4)
            rr = R + 18 if k % 4 in (1, 2) else R - 10
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col + (255,))
        d.ellipse([cx - R * 0.62, cy - R * 0.62, cx + R * 0.62, cy + R * 0.62], fill=(48, 30, 92, 255))
        for k in range(5):
            a = ang + TAU * k / 5
            d.line([(cx, cy), (cx + R * 0.62 * math.cos(a), cy + R * 0.62 * math.sin(a))], fill=col + (255,), width=14)
        d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=col + (255,))

    @staticmethod
    def draw(d, L, t, P, grad):
        g = P["g"]; teeth_moved = P["shift"] * t / DUR   # every gear advances the same number of teeth
        dirs = [1, -1, -1]
        offs = [0, math.pi / 12, math.pi / 16]
        for i, (teeth, R, x, y) in enumerate(g):
            ang = dirs[i] * TAU * teeth_moved / teeth + offs[i]
            Gears.gear(d, x, y, teeth, R, ang, grad(i / 2))

    @staticmethod
    def events(P):
        return [(k * DUR / (P["shift"] * 2), 60 + (k % 2) * 7, 0.12) for k in range(P["shift"] * 2)]


# ---------------------------------------------------------------- Galton board
@concept("galton", "Watch the bell curve appear.", "ocean")
class Galton:
    @staticmethod
    def prep(rnd):
        rows, n = 9, 110
        paths = [[rnd.random() < 0.5 for _ in range(rows)] for _ in range(n)]
        return {"rows": rows, "n": n, "paths": paths}

    @staticmethod
    def geo(P):
        rows = P["rows"]; sx, sy, top = 72, 58, 640
        return rows, sx, sy, top

    @staticmethod
    def draw(d, L, t, P, grad):
        rows, sx, sy, top = Galton.geo(P)
        for r in range(rows):
            for c in range(r + 1):
                x = CX + (c - r / 2) * sx; y = top + r * sy
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(190, 180, 240, 200))
        bins_y = top + rows * sy + 20
        for b in range(rows + 2):
            x = CX + (b - (rows + 1) / 2) * sx
            d.line([(x, bins_y), (x, 1470)], fill=(120, 100, 180, 160), width=3)
        counts = [0] * (rows + 1)
        fall = 1.4
        for i, path in enumerate(P["paths"]):
            t0 = i * 5.0 / P["n"]
            u = (t - t0) / fall
            final = sum(path)
            col = grad(final / rows)
            if u >= 1:
                k = counts[final]; counts[final] += 1
                x = CX + (final - rows / 2) * sx; y = 1460 - 14 - k * 22
                d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col + (255,))
            elif u > 0:
                seg = u * (rows + 1); r = int(seg); f = seg - r
                pos = sum(path[:r]) if r <= rows else final
                if r < rows:
                    x0 = CX + (pos - r / 2) * sx; y0 = top + r * sy - 16
                    nxt = pos + (1 if path[r] else 0)
                    x1 = CX + (nxt - (r + 1) / 2) * sx; y1 = top + (r + 1) * sy - 16
                    x, y = lerp(x0, x1, f), lerp(y0, y1, f) - 18 * math.sin(math.pi * f)
                else:
                    x = CX + (final - rows / 2) * sx; y = lerp(top + rows * sy, 1460 - counts[final] * 22, f)
                d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col + (255,))

    @staticmethod
    def events(P):
        rows = P["rows"]; ev = []
        for i, path in enumerate(P["paths"]):
            if i % 3: continue
            ev.append((i * 5.0 / P["n"] + 1.4, note(sum(path), 69), 0.07))
        return ev


# ---------------------------------------------------------------- Sand art
@concept("sand", "Layer by layer...", "sunset")
class Sand:
    @staticmethod
    def prep(rnd):
        # grains settle into a mound, layered in colour bands
        n = 1100; grains = []
        width = 46; heights = [0] * width
        for i in range(n):
            # drop near the centre with a little spread, then roll to the lowest neighbour
            c = int(width / 2 + rnd.gauss(0, 5)); c = max(1, min(width - 2, c))
            for _ in range(30):
                l, r = heights[c - 1], heights[c + 1]
                if heights[c] - min(l, r) >= 2:
                    c = c - 1 if l < r or (l == r and rnd.random() < 0.5) else c + 1
                    c = max(1, min(width - 2, c))
                else: break
            grains.append((c, heights[c])); heights[c] += 1
        return {"grains": grains, "width": width}

    @staticmethod
    def draw(d, L, t, P, grad):
        g, wdt = P["grains"], P["width"]
        cell = (X1 - X0) / wdt
        n = len(g); shown = int(n * min(1.0, t / 5.6))
        base = 1470
        d.polygon([(CX - 60, 600), (CX + 60, 600), (CX + 8, 660), (CX - 8, 660)], fill=(180, 170, 230, 200))
        for i in range(shown):
            c, h = g[i]
            x = X0 + c * cell; y = base - (h + 1) * cell * 0.8
            col = grad((i // 110) % 10 / 9)
            d.rectangle([x, y, x + cell, y + cell * 0.8 + 1], fill=col + (255,))
        if t < 5.6:  # falling stream
            col = grad((shown // 110) % 10 / 9)
            d.line([(CX, 660), (CX, base - 40)], fill=col + (200,), width=6)

    @staticmethod
    def events(P):
        return [(k * 0.4, note(k % 7, 64), 0.05) for k in range(14)]


# ---------------------------------------------------------------- Dominoes
@concept("dominoes", "One push is all it takes.", "candy")
class Dominoes:
    @staticmethod
    def prep(rnd):
        return {"rows": 3, "per": 13}

    @staticmethod
    def draw(d, L, t, P, grad):
        rows, per = P["rows"], P["per"]
        n = rows * per; dt = 5.2 / n
        h, w = 150, 24
        gap = (X1 - X0 - 60) / (per - 1)
        for k in range(n):
            row, idx = divmod(k, per)
            if row % 2: idx = per - 1 - idx
            sign = 1 if row % 2 == 0 else -1
            bx = X0 + 30 + idx * gap; by = 760 + row * 300
            u = ease((t - 0.3 - k * dt) / 0.35)
            ang = sign * u * math.radians(64)
            # rotate around the bottom corner in the falling direction
            px = bx + sign * w / 2
            pts = [(-w / 2, 0), (w / 2, 0), (w / 2, -h), (-w / 2, -h)]
            out = []
            for x, y in pts:
                x -= sign * w / 2
                xr = x * math.cos(ang) - y * math.sin(ang); yr = x * math.sin(ang) + y * math.cos(ang)
                out.append((px + xr, by + yr))
            d.polygon(out, fill=grad(k / (n - 1)) + (255,))
            d.line([(X0, by + 2), (X1, by + 2)], fill=(120, 100, 180, 120), width=3)

    @staticmethod
    def events(P):
        n = P["rows"] * P["per"]; dt = 5.2 / n
        return [(0.3 + k * dt + 0.2, 90 + (k % 3), 0.07) for k in range(n)]


# ---------------------------------------------------------------- Corner bounce
@concept("corner", "Will it hit the corner?", "neon")
class Corner:
    @staticmethod
    def prep(rnd): return {"a": 5, "b": 4}

    @staticmethod
    def tri(x):
        x = x % 1.0
        return 2 * x if x < 0.5 else 2 - 2 * x

    @staticmethod
    def draw(d, L, t, P, grad):
        bx0, by0, bx1, by1 = X0, 600, X1, 1460
        s = 120
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=8, outline=(150, 130, 220, 200), width=4)
        tt = min(t, 6.0)
        # x bounces a times and y b times by t=6, so both hit a wall together - the corner - only at t=6
        u = Corner.tri(tt * P["a"] / 12.0)
        v = Corner.tri(tt * P["b"] / 12.0)
        x = bx0 + (bx1 - bx0 - s) * u; y = by0 + (by1 - by0 - s) * v
        col = grad((t / DUR) % 1.0)
        for g in range(8, 0, -1):  # trail
            tg = max(0.0, tt - g * 0.03)
            ug = Corner.tri(tg * P["a"] / 12.0); vg = Corner.tri(tg * P["b"] / 12.0)
            xg = bx0 + (bx1 - bx0 - s) * ug; yg = by0 + (by1 - by0 - s) * vg
            d.rounded_rectangle([xg, yg, xg + s, yg + s], radius=24, fill=col + (18,))
        d.rounded_rectangle([x, y, x + s, y + s], radius=24, fill=col + (255,))
        if t >= 6.0:
            a = 1 - (t - 6.0)
            d.rounded_rectangle([bx0, by0, bx1, by1], radius=8, outline=(255, 255, 255, int(255 * a)), width=14)

    @staticmethod
    def events(P):
        ev = []
        for k in range(1, P["a"] + 1):
            ev.append((k * 6.0 / P["a"], 76, 0.09))
        for k in range(1, P["b"] + 1):
            ev.append((k * 6.0 / P["b"], 79, 0.09))
        ev += [(6.0, 84, 0.25), (6.0, 88, 0.2), (6.05, 91, 0.2)]
        return ev


# ---------------------------------------------------------------- Maze solver
@concept("maze", "Finding the way out...", "aurora")
class Maze:
    @staticmethod
    def prep(rnd):
        cw, ch = 15, 15
        walls = {(x, y): [True, True, True, True] for x in range(cw) for y in range(ch)}  # N E S W
        seen = {(0, 0)}; stack = [(0, 0)]
        dirs = [(0, -1, 0, 2), (1, 0, 1, 3), (0, 1, 2, 0), (-1, 0, 3, 1)]
        while stack:
            x, y = stack[-1]
            opts = [(x + dx, y + dy, a, b) for dx, dy, a, b in dirs if (x + dx, y + dy) in walls and (x + dx, y + dy) not in seen]
            if not opts: stack.pop(); continue
            nx, ny, a, b = rnd.choice(opts)
            walls[(x, y)][a] = False; walls[(nx, ny)][b] = False
            seen.add((nx, ny)); stack.append((nx, ny))
        # BFS solution from top-left to bottom-right
        from collections import deque
        prev = {(0, 0): None}; q = deque([(0, 0)])
        while q:
            c = q.popleft()
            for dx, dy, a, _ in dirs:
                nb = (c[0] + dx, c[1] + dy)
                if nb in walls and not walls[c][a] and nb not in prev: prev[nb] = c; q.append(nb)
        path = []; c = (cw - 1, ch - 1)
        while c: path.append(c); c = prev[c]
        return {"walls": walls, "path": path[::-1], "cw": cw, "ch": ch}

    @staticmethod
    def draw(d, L, t, P, grad):
        cw, ch = P["cw"], P["ch"]; s = (X1 - X0) / cw; oy = 1000 - s * ch / 2
        for (x, y), w in P["walls"].items():
            x0, y0 = X0 + x * s, oy + y * s
            col = (150, 130, 220, 220)
            if w[0]: d.line([(x0, y0), (x0 + s, y0)], fill=col, width=4)
            if w[1]: d.line([(x0 + s, y0), (x0 + s, y0 + s)], fill=col, width=4)
            if w[2]: d.line([(x0, y0 + s), (x0 + s, y0 + s)], fill=col, width=4)
            if w[3]: d.line([(x0, y0), (x0, y0 + s)], fill=col, width=4)
        path = P["path"]; k = int(len(path) * min(1.0, max(0.0, (t - 0.6) / 4.6)))
        pts = [(X0 + (x + 0.5) * s, oy + (y + 0.5) * s) for x, y in path[:max(1, k)]]
        for j in range(1, len(pts)):
            d.line([pts[j - 1], pts[j]], fill=grad(j / len(path)) + (255,), width=int(s * 0.42))
        hx, hy = pts[-1]
        d.ellipse([hx - s * 0.3, hy - s * 0.3, hx + s * 0.3, hy + s * 0.3], fill=(255, 255, 255, 255))
        if t > 5.3:
            a = min(1.0, (t - 5.3) / 0.3) * (1 - max(0.0, (t - 6.5) / 0.5))
            ex, ey = X0 + (cw - 0.5) * s, oy + (ch - 0.5) * s
            d.ellipse([ex - s, ey - s, ex + s, ey + s], outline=(255, 255, 255, int(255 * a)), width=6)

    @staticmethod
    def events(P):
        n = len(P["path"])
        return [(0.6 + 4.6 * j / n, note(j % 10, 67), 0.04) for j in range(0, n, 3)] + [(5.25, 84, 0.2), (5.3, 91, 0.15)]


# ---------------------------------------------------------------- Fireworks
@concept("fireworks", "Turn the sound on.", "neon")
class Fireworks:
    @staticmethod
    def prep(rnd):
        shows = []
        for i in range(5):
            t0 = 0.3 + i * 1.15
            x = rnd.uniform(220, 860); y = rnd.uniform(680, 960)
            parts = [(rnd.uniform(0, TAU), rnd.uniform(170, 340)) for _ in range(110)]
            shows.append((t0, x, y, parts, i / 4))
        return {"shows": shows}

    @staticmethod
    def draw(d, L, t, P, grad):
        for t0, x, y, parts, cu in P["shows"]:
            rise = 0.6
            if t0 <= t < t0 + rise:
                u = ease((t - t0) / rise)
                yy = lerp(1480, y, u)
                d.ellipse([x - 6, yy - 6, x + 6, yy + 6], fill=(255, 240, 200, 255))
                d.line([(x, yy), (x, yy + 60)], fill=(255, 220, 160, 120), width=4)
            te = t - t0 - rise
            if 0 <= te < 2.4:
                for ang, sp in parts:
                    for g in (0.0, 0.06, 0.12):
                        tg = max(0.0, te - g)
                        dist = sp * (1 - math.exp(-2.2 * tg)) / 1.0
                        px = x + dist * math.cos(ang); py = y + dist * math.sin(ang) + 60 * tg * tg
                        a = max(0.0, 1 - te / 2.4) ** 0.7 * (1.0 if g == 0 else 0.45)
                        rr = 10 if g == 0 else 6
                        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=grad(cu) + (int(255 * a),))

    @staticmethod
    def events(P):
        ev = []
        for i, (t0, *_rest) in enumerate(P["shows"]):
            ev += [(t0 + 0.6, 48, 0.3), (t0 + 0.62, note(i * 2, 79), 0.12), (t0 + 0.8, note(i * 2 + 2, 79), 0.06)]
        return ev


# ---------------------------------------------------------------- Growing tree
@concept("tree", "Watch it grow.", "aurora")
class Tree:
    @staticmethod
    def prep(rnd):
        segs = []
        def grow(x, y, ang, ln, depth):
            if depth > 9: return
            x2, y2 = x + ln * math.cos(ang), y + ln * math.sin(ang)
            segs.append((x, y, x2, y2, depth))
            spread = 0.42 + rnd.uniform(-0.08, 0.08)
            grow(x2, y2, ang - spread, ln * rnd.uniform(0.68, 0.78), depth + 1)
            grow(x2, y2, ang + spread, ln * rnd.uniform(0.68, 0.78), depth + 1)
        grow(CX, 1470, -math.pi / 2, 230, 0)
        return {"segs": segs}

    @staticmethod
    def draw(d, L, t, P, grad):
        sway = 0.012 * math.sin(TAU * t / DUR * 2)
        for x, y, x2, y2, dep in P["segs"]:
            t0 = 0.2 + dep * 0.45
            u = ease((t - t0) / 0.5)
            if u <= 0: continue
            off = sway * (dep ** 1.5) * 20
            xe, ye = lerp(x, x2, u) + off, lerp(y, y2, u)
            wdt = max(2, int(20 * (0.72 ** dep)))
            d.line([(x + sway * ((dep - 1) ** 1.5 if dep else 0) * 20, y), (xe, ye)], fill=grad(dep / 10) + (255,), width=wdt)
            if dep == 9 and u >= 1:
                b = ease((t - 4.9) / 0.6)
                if b > 0:
                    r = 9 * b
                    d.ellipse([xe - r, ye - r, xe + r, ye + r], fill=grad(1.0) + (230,))

    @staticmethod
    def events(P):
        return [(0.2 + dep * 0.45, note(dep, 60), 0.09) for dep in range(10)] + [(4.9 + k * 0.08, note(k + 5, 72), 0.05) for k in range(8)]


# ---------------------------------------------------------------- Hilbert curve
@concept("hilbert", "One line. No crossings.", "candy")
class Hilbert:
    @staticmethod
    def prep(rnd):
        order = 5; n = 2 ** order
        def d2xy(dd):
            x = y = 0; s = 1; t_ = dd
            while s < n:
                rx = 1 & (t_ // 2); ry = 1 & (t_ ^ rx)
                if ry == 0:
                    if rx == 1: x, y = s - 1 - x, s - 1 - y
                    x, y = y, x
                x += s * rx; y += s * ry; t_ //= 4; s *= 2
            return x, y
        return {"pts": [d2xy(i) for i in range(n * n)], "n": n}

    @staticmethod
    def draw(d, L, t, P, grad):
        n = P["n"]; s = (X1 - X0) / n; oy = 1000 - (X1 - X0) / 2
        pts = P["pts"]; k = int(len(pts) * min(1.0, t / 5.8))
        xy = [(X0 + (x + 0.5) * s, oy + (y + 0.5) * s) for x, y in pts[:max(2, k)]]
        for j in range(1, len(xy)):
            d.line([xy[j - 1], xy[j]], fill=grad(j / len(pts)) + (255,), width=int(s * 0.45))
        if t < 5.8:
            hx, hy = xy[-1]; d.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], fill=(255, 255, 255, 255))

    @staticmethod
    def events(P):
        return [(5.8 * k / 24, note(k % 10, 67), 0.05) for k in range(24)] + [(5.8, 84, 0.15)]


# ---------------------------------------------------------------- Circle packing
@concept("packing", "Every gap, filled.", "brand")
class Packing:
    @staticmethod
    def prep(rnd):
        R = 430; circles = []
        tries = 0
        while len(circles) < 170 and tries < 40000:
            tries += 1
            a = rnd.uniform(0, TAU); rr = R * math.sqrt(rnd.random())
            x, y = CX + rr * math.cos(a), CY + rr * math.sin(a)
            m = R - math.hypot(x - CX, y - CY)
            for cx_, cy_, r_ in circles:
                m = min(m, math.hypot(x - cx_, y - cy_) - r_)
                if m < 8: break
            if m >= 8: circles.append((x, y, min(m - 3, 110)))
        circles.sort(key=lambda c: -c[2])
        return {"c": circles}

    @staticmethod
    def draw(d, L, t, P, grad):
        c = P["c"]; n = len(c)
        d.ellipse([CX - 434, CY - 434, CX + 434, CY + 434], outline=(150, 130, 220, 160), width=3)
        for i, (x, y, r) in enumerate(c):
            t0 = 5.4 * (i / n) ** 0.8
            u = (t - t0) / 0.25
            if u <= 0: continue
            sc = 1 + 0.15 * math.sin(math.pi * min(1.0, u)) if u < 1 else 1.0
            rr = r * min(1.0, u) * sc
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=grad((i * 0.618) % 1.0) + (255,))

    @staticmethod
    def events(P):
        n = len(P["c"])
        return [(5.4 * (i / n) ** 0.8, note(i % 10, 72 - (2 if i < 10 else 0)), 0.05) for i in range(0, n, 4)]


# ---------------------------------------------------------------- Times-table string art
@concept("stringart", "It's just multiplication.", "aurora")
class StringArt:
    @staticmethod
    def prep(rnd): return {"n": 200, "m0": 2.0, "m1": 3.0}

    @staticmethod
    def draw(d, L, t, P, grad):
        n = P["n"]; R = 420
        m = P["m0"] + (P["m1"] - P["m0"]) * (0.5 - 0.5 * math.cos(TAU * t / DUR))
        for i in range(n):
            a1 = TAU * i / n - math.pi / 2; a2 = TAU * (i * m) / n - math.pi / 2
            d.line([(CX + R * math.cos(a1), CY + R * math.sin(a1)), (CX + R * math.cos(a2), CY + R * math.sin(a2))],
                   fill=grad(i / n) + (150,), width=2)
        d.ellipse([CX - R, CY - R, CX + R, CY + R], outline=(200, 190, 240, 120), width=3)

    @staticmethod
    def events(P):
        return [(k * DUR / 8, note([0, 2, 4, 2, 5, 4, 2, 1][k], 67), 0.07) for k in range(8)]


# ---------------------------------------------------------------- Kaleidoscope
@concept("kaleido", "Stare into the middle.", "sunset")
class Kaleido:
    @staticmethod
    def prep(rnd):
        shapes = [(rnd.uniform(60, 400), rnd.uniform(0, 0.39), rnd.uniform(18, 60), rnd.randint(0, 2), rnd.random(), rnd.choice([1, 2, -1]))
                  for _ in range(14)]
        return {"shapes": shapes, "fold": 8}

    @staticmethod
    def draw(d, L, t, P, grad):
        F = P["fold"]; T = TAU * t / DUR
        for dist, ang, size, kind, cu, spd in P["shapes"]:
            dd = dist * (0.8 + 0.2 * math.sin(T * 2 + cu * 6))
            for k in range(F):
                for mirror in (1, -1):
                    a = TAU * k / F + mirror * (ang + 0.25 * math.sin(T * spd)) + T / 4
                    x, y = CX + dd * math.cos(a), CY + dd * math.sin(a)
                    col = grad(cu) + (210,)
                    if kind == 0: d.ellipse([x - size, y - size, x + size, y + size], fill=col)
                    elif kind == 1:
                        pts = [(x + size * math.cos(a + j * TAU / 3), y + size * math.sin(a + j * TAU / 3)) for j in range(3)]
                        d.polygon(pts, fill=col)
                    else: d.ellipse([x - size, y - size, x + size, y + size], outline=col, width=5)

    @staticmethod
    def events(P):
        return [(k * DUR / 7, note([0, 4, 2, 7, 4, 9, 7][k], 69), 0.06) for k in range(7)]


# ---------------------------------------------------------------- numpy field helper
def _field_to_layer(L, field_rgba, box):
    """paste a small RGBA uint8 array, scaled smoothly into box=(x0,y0,x1,y1)."""
    im = Image.fromarray(field_rgba, "RGBA").resize((box[2] - box[0], box[3] - box[1]), Image.BICUBIC)
    L.alpha_composite(im, (box[0], box[1]))


def _pal_lut(grad, n=256):
    return np.array([grad(i / (n - 1)) for i in range(n)], dtype=np.float32)


# ---------------------------------------------------------------- Water ripples
@concept("ripples", "Two drops. One pattern.", "ocean")
class Ripples:
    @staticmethod
    def prep(rnd): return {"src": [(-0.28, -0.1), (0.3, 0.15)], "k": 34.0}

    @staticmethod
    def draw(d, L, t, P, grad):
        w, h = 180, 180
        ys, xs = np.mgrid[-1:1:h * 1j, -1:1:w * 1j]
        T = TAU * t / DUR
        f = np.zeros_like(xs)
        for sx, sy in P["src"]:
            r = np.hypot(xs - sx, ys - sy)
            f += np.sin(P["k"] * r - 4 * T) / (1 + 3 * r)
        f = (f - f.min()) / (np.ptp(f) + 1e-9)
        lut = _pal_lut(grad)
        rgb = lut[(f * 255).astype(int)]
        mask = (np.hypot(xs, ys) < 0.98).astype(np.float32)
        a = (mask * (90 + 165 * f)).astype(np.uint8)
        arr = np.dstack([rgb.astype(np.uint8), a])
        _field_to_layer(L, arr, (CX - 440, CY - 440, CX + 440, CY + 440))

    @staticmethod
    def events(P):
        return [(k * DUR / 8, note([4, 2, 0, 2][k % 4], 72), 0.08) for k in range(8)]


# ---------------------------------------------------------------- Lava lamp (metaballs)
@concept("lava", "Lava lamp vibes.", "sunset")
class Lava:
    @staticmethod
    def prep(rnd):
        return {"blobs": [(rnd.uniform(0.15, 0.3), rnd.choice([1, 2]), rnd.choice([1, 2, 3]), rnd.uniform(0, TAU), rnd.uniform(0.25, 0.45)) for _ in range(7)]}

    @staticmethod
    def draw(d, L, t, P, grad):
        w, h = 120, 180
        ys, xs = np.mgrid[0:1:h * 1j, 0:1:w * 1j]
        T = TAU * t / DUR
        f = np.zeros_like(xs)
        for r, fx, fy, ph, ax in P["blobs"]:
            bx = 0.5 + ax * math.sin(fx * T + ph); by = 0.5 + 0.38 * math.sin(fy * T + ph * 1.7)
            f += (r * 0.55) ** 2 / ((xs - bx) ** 2 + ((ys - by) * 1.5) ** 2 + 1e-4)
        inside = np.clip((f - 1.0) * 3, 0, 1)
        lut = _pal_lut(grad)
        rgb = lut[np.clip(ys * 255, 0, 255).astype(int)]
        arr = np.dstack([rgb.astype(np.uint8), (inside * 255).astype(np.uint8)])
        x0, y0 = CX - 300, 570
        d.rounded_rectangle([x0 - 10, y0 - 10, x0 + 610, y0 + 910], radius=60, outline=(170, 150, 230, 180), width=5)
        _field_to_layer(L, arr, (x0, y0, x0 + 600, y0 + 900))

    @staticmethod
    def events(P):
        return [(k * DUR / 4, note([0, 4, 2, 7][k], 60), 0.08) for k in range(4)]


# ---------------------------------------------------------------- Growing cells (Voronoi)
@concept("cells", "Everything finds its place.", "candy")
class Cells:
    @staticmethod
    def prep(rnd):
        return {"seeds": [(rnd.uniform(0.04, 0.96), rnd.uniform(0.04, 0.96), rnd.uniform(0, 1.6)) for _ in range(34)]}

    @staticmethod
    def draw(d, L, t, P, grad):
        w = h = 220
        ys, xs = np.mgrid[0:1:h * 1j, 0:1:w * 1j]
        seeds = P["seeds"]
        dist = np.full(xs.shape, 9.0); idx = np.full(xs.shape, -1)
        for i, (sx, sy, t0) in enumerate(seeds):
            dd = np.hypot(xs - sx, ys - sy)
            grow = max(0.0, (t - t0) * 0.09)
            ok = (dd < grow) & (dd < dist)
            dist = np.where(ok, dd, dist); idx = np.where(ok, i, idx)
        lut = _pal_lut(grad, len(seeds))
        rgb = lut[np.clip(idx, 0, None)]
        a = np.where(idx >= 0, 235, 0).astype(np.uint8)
        # darker cell borders
        edge = np.zeros_like(a, dtype=bool)
        edge[1:, :] |= idx[1:, :] != idx[:-1, :]; edge[:, 1:] |= idx[:, 1:] != idx[:, :-1]
        rgb = np.where(edge[..., None] & (idx[..., None] >= 0), rgb * 0.45, rgb)
        arr = np.dstack([rgb.astype(np.uint8), a])
        _field_to_layer(L, arr, (X0, CY - 450, X1, CY + 450))

    @staticmethod
    def events(P):
        return [(t0, note(i % 10, 69), 0.05) for i, (_, _, t0) in enumerate(P["seeds"])]


# ---------------------------------------------------------------- Bubbles
@concept("bubbles", "Pop, pop, pop...", "ocean")
class Bubbles:
    @staticmethod
    def prep(rnd):
        return {"b": [(rnd.uniform(X0 + 60, X1 - 60), rnd.uniform(0, DUR), rnd.uniform(26, 70), rnd.uniform(0, TAU), rnd.uniform(1.6, 2.6)) for _ in range(26)]}

    @staticmethod
    def draw(d, L, t, P, grad):
        for x, t0, r, ph, life in P["b"]:
            age = (t - t0) % DUR
            if age > life + 0.25: continue
            u = min(1.0, age / life)
            y = lerp(1480, 640, u) ; xx = x + 30 * math.sin(ph + age * 3)
            col = grad(r / 70)
            if age <= life:
                d.ellipse([xx - r, y - r, xx + r, y + r], outline=col + (230,), width=4)
                d.ellipse([xx - r * 0.5, y - r * 0.6, xx - r * 0.1, y - r * 0.25], fill=(255, 255, 255, 140))
            else:  # pop ring
                pu = (age - life) / 0.25
                rr = r * (1 + pu)
                for k in range(8):
                    a = TAU * k / 8
                    d.line([(xx + rr * 0.8 * math.cos(a), y + rr * 0.8 * math.sin(a)), (xx + rr * math.cos(a), y + rr * math.sin(a))],
                           fill=col + (int(255 * (1 - pu)),), width=4)

    @staticmethod
    def events(P):
        return [((t0 + life) % DUR, note(int(r) % 10, 74), 0.08) for x, t0, r, ph, life in P["b"]]


# ---------------------------------------------------------------- Paint drops
@concept("paint", "Drop by drop.", "neon")
class Paint:
    @staticmethod
    def prep(rnd): return {"drops": 14}

    @staticmethod
    def draw(d, L, t, P, grad):
        n = P["drops"]; dt = 5.6 / n
        # each new drop lands in the centre and pushes the older rings outward
        k = int(t / dt)
        rings = []
        for i in range(min(k + 1, n)):
            age = t - i * dt
            if age < 0: continue
            area = min(1.0, age / 0.45)
            rings.append((i, area))
        # radius of each ring = sqrt(cumulative area of it and all newer drops)
        total = 0.0; radii = []
        for i, area in reversed(rings):
            total += area; radii.append((i, 108 * math.sqrt(total)))
        for i, r in sorted(radii, key=lambda z: -z[1]):
            d.ellipse([CX - r, CY - r, CX + r, CY + r], fill=grad((i % 7) / 6) + (255,))
        if k < n:
            u = (t - k * dt) / dt
            y = lerp(600, CY, min(1.0, u * 2.2))
            if u < 0.45:
                d.ellipse([CX - 20, y - 26, CX + 20, y + 14], fill=grad((k % 7) / 6) + (255,))

    @staticmethod
    def events(P):
        n = P["drops"]; dt = 5.6 / n
        return [(i * dt + dt * 0.45, note(i % 10, 67), 0.09) for i in range(n)]


# ---------------------------------------------------------------- Particles assemble the logo
@concept("assemble", "Wait for it...", "brand")
class Assemble:
    @staticmethod
    @lru_cache(maxsize=1)
    def target():
        import os
        logo = Image.open(os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")).convert("RGB").resize((70, 70))
        arr = np.asarray(logo).astype(int)
        pts = []
        for y in range(70):
            for x in range(70):
                r, g, b = arr[y, x]
                if r > 150 and g > 100:            # the cookie
                    pts.append((x, y, (int(r), int(g), int(b))))
                elif r < 60 and g < 40 and b < 80 and (x - 35) ** 2 + (y - 35) ** 2 < 23 ** 2:  # the '?' and chips
                    pts.append((x, y, (60, 30, 100)))
        return pts

    @staticmethod
    def prep(rnd):
        pts = Assemble.target()
        starts = [(rnd.uniform(X0, X1), rnd.uniform(620, 1460), rnd.uniform(0, 1.2)) for _ in pts]
        return {"starts": starts}

    @staticmethod
    def draw(d, L, t, P, grad):
        pts = Assemble.target(); s = 11.5
        ox, oy = CX - 35 * s, CY - 35 * s
        for (x, y, col), (sx, sy, delay) in zip(pts, P["starts"]):
            u = ease((t - 0.8 - delay) / 2.6)
            out = ease((t - 6.1) / 0.8)  # scatter back out at the end so the loop restarts cleanly
            tx, ty = ox + x * s, oy + y * s
            px, py = lerp(sx, tx, u), lerp(sy, ty, u)
            px, py = lerp(px, sx, out), lerp(py, sy, out)
            c = tuple(int(lerp(a, b, u)) for a, b in zip(grad(delay / 1.2), col))
            r = lerp(4, s * 0.55, u)
            d.ellipse([px - r, py - r, px + r, py + r], fill=c + (255,))

    @staticmethod
    def events(P):
        return [(0.8 + k * 0.25, note(k, 64), 0.05) for k in range(14)] + [(4.6, 84, 0.2), (4.65, 88, 0.15), (4.7, 91, 0.15)]


# ---------------------------------------------------------------- Globe of dots
@concept("globe", "A world of dots.", "aurora")
class Globe:
    @staticmethod
    def prep(rnd):
        n = 700; pts = []
        g = math.pi * (3 - math.sqrt(5))
        for i in range(n):
            y = 1 - 2 * (i + 0.5) / n; r = math.sqrt(1 - y * y); th = g * i
            pts.append((r * math.cos(th), y, r * math.sin(th)))
        return {"pts": pts}

    @staticmethod
    def draw(d, L, t, P, grad):
        T = TAU * t / DUR; tilt = 0.4
        R = 400
        items = []
        for x, y, z in P["pts"]:
            xr = x * math.cos(T) + z * math.sin(T); zr = -x * math.sin(T) + z * math.cos(T)
            yr = y * math.cos(tilt) - zr * math.sin(tilt); zr2 = y * math.sin(tilt) + zr * math.cos(tilt)
            items.append((zr2, xr, yr, y))
        for zr, xr, yr, y in sorted(items):
            depth = (zr + 1) / 2
            r = 3 + 7 * depth
            col = grad((y + 1) / 2)
            d.ellipse([CX + R * xr - r, CY + R * yr - r, CX + R * xr + r, CY + R * yr + r], fill=col + (int(60 + 195 * depth),))

    @staticmethod
    def events(P):
        return [(k * DUR / 6, note([0, 2, 4, 7, 4, 2][k], 64), 0.08) for k in range(6)]


# ---------------------------------------------------------------- Stacking blocks
@concept("blocks", "Perfect fit, every time.", "candy")
class Blocks:
    @staticmethod
    def prep(rnd):
        cols, rows = 9, 10
        order = []
        heights = [0] * cols
        while len(order) < cols * rows:
            c = rnd.randrange(cols)
            if heights[c] < rows and (heights[c] <= min(heights) + 1):
                order.append((c, heights[c])); heights[c] += 1
        return {"order": order, "cols": cols, "rows": rows}

    @staticmethod
    def draw(d, L, t, P, grad):
        cols, rows = P["cols"], P["rows"]; s = (X1 - X0) / cols
        base = 1470; n = len(P["order"]); dt = 5.2 / n
        flash = max(0.0, 1 - abs(t - 5.6) / 0.3) if t > 5.3 else 0
        for i, (c, h) in enumerate(P["order"]):
            u = (t - i * dt) / 0.28
            if u <= 0: continue
            ty = base - (h + 1) * s * 0.9
            y = lerp(560, ty, min(1.0, u) ** 2)
            col = grad(h / (rows - 1))
            col = tuple(int(min(255, ch + 90 * flash)) for ch in col)
            d.rounded_rectangle([X0 + c * s + 4, y + 4, X0 + (c + 1) * s - 4, y + s * 0.9 - 4], radius=12, fill=col + (255,))

    @staticmethod
    def events(P):
        n = len(P["order"]); dt = 5.2 / n
        return [(i * dt + 0.28, note(h, 60), 0.05) for i, (c, h) in enumerate(P["order"]) if i % 2 == 0] + [(5.6, 84, 0.2)]
