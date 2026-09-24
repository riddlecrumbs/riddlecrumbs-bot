"""Original soundtrack for every reel, generated from scratch (so there is nothing to copyright-claim).

  * a short music bed (one of several styles, picked per reel), 120 BPM so 7 s = 14 beats and it loops cleanly
  * sound effects locked to the on-screen animation: countdown ticks, reveal chimes, whooshes, pops, key clicks
"""
import wave
import numpy as np

SR = 44100
DUR = 7.0
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM


def _t(n): return np.arange(n) / SR


def _env(n, attack=0.005, decay=0.2):
    t = _t(n)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4))


def _place(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= buf.shape[0]: return
    j = min(buf.shape[0], i + len(sig))
    s = sig[: j - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:j, 0] += s * l * 1.414
    buf[i:j, 1] += s * r * 1.414


def midi(m): return 440.0 * 2 ** ((m - 69) / 12)


# ---------------- instruments ----------------
def kick():
    n = int(0.28 * SR); t = _t(n)
    f = 45 + 95 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)


def hat(rng, open_=False):
    n = int((0.12 if open_ else 0.04) * SR)
    x = rng.standard_normal(n)
    x = x - np.concatenate([[0], x[:-1]])          # crude high-pass
    return x * _env(n, 0.001, 0.05 if open_ else 0.012) * 0.25


def clap(rng):
    n = int(0.18 * SR)
    x = rng.standard_normal(n)
    x = x - np.concatenate([[0], x[:-1]])
    e = np.zeros(n)
    for off in (0, 0.01, 0.02):
        k = int(off * SR); e[k:] += _env(n - k, 0.001, 0.04 if off < 0.02 else 0.09)
    return x * e * 0.18


def pluck(freq, dur, shape="tri", decay=0.25):
    n = int(dur * SR); t = _t(n)
    ph = (freq * t) % 1.0
    if shape == "tri": w = 2 * np.abs(2 * ph - 1) - 1
    elif shape == "square": w = np.sign(ph - 0.5) * 0.6
    elif shape == "mallet":  # marimba-ish: fundamental + 4th partial, quick decay
        w = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t / 0.03)
    else: w = np.sin(2 * np.pi * freq * t)
    return w * _env(n, 0.003, decay)


def keys(freqs, dur):
    """soft electric-piano-ish chord (sines with slight detune + tremolo)."""
    n = int(dur * SR); t = _t(n)
    s = np.zeros(n)
    for f in freqs:
        s += np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t) + 0.12 * np.sin(2 * np.pi * f * 2 * t)
    trem = 1 - 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.5 * t))
    return s * trem * _env(n, 0.02, dur * 0.8) / len(freqs)


def bass(freq, dur):
    n = int(dur * SR); t = _t(n)
    w = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)
    return np.tanh(1.5 * w) * _env(n, 0.005, dur * 0.6)


# ---------------- music beds ----------------
# chord degrees (semitones from root) for I, V, vi, IV
CHORDS = {"I": [0, 4, 7], "V": [7, 11, 14], "vi": [9, 12, 16], "IV": [5, 9, 12]}
PROG = ["I", "V", "vi", "IV", "I", "V", "IV"]  # 7 chords x 2 beats = 14 beats = 7 s, IV -> I on loop

STYLES = ["bounce", "lofi", "mallet"]


def pad(freqs, dur):
    n = int(dur * SR); t = _t(n)
    s = np.zeros(n)
    for f in freqs:
        s += np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 1.004 * t) + 0.15 * np.sin(2 * np.pi * f * 0.5 * t)
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 0.35, 0, 1)
    return s * env / len(freqs)


def music(style, root_midi, rng):
    buf = np.zeros((N, 2))
    if style == "ambient":   # soft evolving pad, no drums - for the relaxing loops
        for ci, name in enumerate(PROG):
            notes = [midi(root_midi + d - 12) for d in CHORDS[name]]
            _place(buf, pad(notes, 2 * BEAT + 0.35), ci * 2 * BEAT, 0.30)
            _place(buf, bass(midi(root_midi + CHORDS[name][0] - 24), 2 * BEAT), ci * 2 * BEAT, 0.18)
        d = int(0.33 * SR)
        echo = np.zeros_like(buf); echo[d:, 0] = buf[:-d, 1]; echo[d:, 1] = buf[:-d, 0]
        return buf + 0.3 * echo
    for ci, name in enumerate(PROG):
        t0 = ci * 2 * BEAT
        notes = [root_midi + d for d in CHORDS[name]]
        # bass: root on each beat (lofi: once per chord)
        broot = midi(root_midi + CHORDS[name][0] - 24)
        if style == "lofi":
            _place(buf, bass(broot, 2 * BEAT), t0, 0.35)
        else:
            for b in range(2):
                _place(buf, bass(broot, BEAT * 0.9), t0 + b * BEAT, 0.30)
        if style == "lofi":
            _place(buf, keys([midi(n) for n in notes], 2 * BEAT), t0, 0.32)
        # arpeggio
        step = {"bounce": BEAT / 2, "chip": BEAT / 4, "mallet": BEAT / 4, "lofi": BEAT}[style]
        shape = {"bounce": "tri", "chip": "square", "mallet": "mallet", "lofi": "sine"}[style]
        pattern = [0, 1, 2, 1] if style != "chip" else [0, 1, 2, 3, 2, 1, 0, 1]
        k = 0; t = t0
        while t < t0 + 2 * BEAT - 1e-6:
            idx = pattern[k % len(pattern)]
            m = notes[idx % 3] + (12 if idx == 3 else 0) + 12
            g = {"bounce": 0.16, "chip": 0.07, "mallet": 0.14, "lofi": 0.10}[style]
            pan = 0.35 if k % 2 else -0.35
            _place(buf, pluck(midi(m), step * 1.8, shape, 0.18 if style != "lofi" else 0.5), t, g, pan)
            t += step; k += 1
    # drums
    for b in range(14):
        tb = b * BEAT
        if style in ("bounce", "chip", "mallet") or b % 2 == 0:
            _place(buf, kick(), tb, 0.55 if style != "lofi" else 0.45)
        if style == "lofi" and b % 2 == 1:
            _place(buf, clap(rng), tb + 0.02, 1.0)
        if style == "bounce" and b % 2 == 1:
            _place(buf, clap(rng), tb, 0.9)
        _place(buf, hat(rng), tb + BEAT / 2, 0.6 if style != "lofi" else 0.45, 0.3)
    if style == "lofi":  # vinyl crackle
        cr = np.zeros(N); idx = rng.integers(0, N, 300); cr[idx] = rng.uniform(-0.3, 0.3, 300)
        buf += np.stack([cr, cr], 1) * 0.3
    # simple stereo echo for space
    d = int(BEAT * 0.75 * SR)
    echo = np.zeros_like(buf); echo[d:, 0] = buf[:-d, 1]; echo[d:, 1] = buf[:-d, 0]
    return buf + 0.22 * echo


# ---------------- sound effects ----------------
def sfx_note(m):
    n = int(0.9 * SR); t = _t(n); f = midi(m)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.08)) * _env(n, 0.002, 0.35)


def sfx_tick():
    n = int(0.06 * SR); t = _t(n)
    return (np.sin(2 * np.pi * 1250 * t) + 0.6 * np.sin(2 * np.pi * 1900 * t)) * _env(n, 0.0005, 0.012)


def sfx_bell(freq=1318.5, dec=0.6):
    n = int(1.2 * SR); t = _t(n)
    s = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / (dec / r ** 0.5))
            for r, a in [(1, 1.0), (2.0, 0.45), (2.76, 0.3), (5.4, 0.12)])
    return s * _env(n, 0.001, 10)


def sfx_correct():
    out = np.zeros(int(1.4 * SR))
    a = sfx_bell(midi(84), 0.4); b = sfx_bell(midi(91), 0.6)
    out[: len(a)] += a
    k = int(0.11 * SR); out[k:k + len(b)] += b[: len(out) - k]
    return out * 0.6


def sfx_whoosh(rng, dur=0.35):
    n = int(dur * SR); t = _t(n)
    x = rng.standard_normal(n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    cut = np.linspace(600, 4000, n)
    y = np.empty(n); acc = 0.0
    for i in range(n):
        a = np.exp(-2 * np.pi * cut[i] / SR)
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y * env * 1.2


def sfx_pop():
    n = int(0.09 * SR); t = _t(n)
    f = 260 + 700 * np.exp(-t / 0.012)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.001, 0.03)


def sfx_blip(i=0):
    n = int(0.07 * SR); t = _t(n)
    f = midi(79 + [0, 2, 4, 7, 9, 12][i % 6])
    return np.sin(2 * np.pi * f * t) * _env(n, 0.001, 0.025)


def sfx_click(rng):
    n = int(0.03 * SR)
    x = rng.standard_normal(n); x = x - np.concatenate([[0], x[:-1]])
    t = _t(n)
    return (x * 0.5 + np.sin(2 * np.pi * 180 * t)) * _env(n, 0.0005, 0.008)


def sfx_boom():
    n = int(0.6 * SR); t = _t(n)
    f = 40 + 120 * np.exp(-t / 0.05)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.18)


def events_for(r):
    """(time, effect, gain) list mirroring engine.py's animation timings."""
    t = r["type"]; ev = []
    if t == "riddle":
        ev += [(1.4 + i, "tick", 0.45) for i in range(4)] + [(5.4, "bell", 0.35), (5.4, "pop", 0.35)]
    elif t == "quiz":
        ev += [(0.15 + 0.1 * i, "blip", 0.22, i) for i in range(4)]
        ev += [(1.4 + i, "tick", 0.45) for i in range(4)] + [(5.2, "correct", 0.55), (6.0, "pop", 0.3)]
    elif t == "maths":
        steps = r["steps"]
        ev += [(s[0], "whoosh", 0.3) for s in steps[1:-1]] + [(steps[-1][0], "bell", 0.35), (5.6, "pop", 0.3)]
    elif t == "fact":
        ev += [(0.35, "boom", 0.6), (0.35, "pop", 0.3), (2.4, "whoosh", 0.3), (5.0, "pop", 0.3)]
    elif t == "stroop":
        ev += [(0.9 + 0.12 * i, "blip", 0.22, i) for i in range(6)] + [(5.3, "pop", 0.3)]
    elif t == "relax":
        import fun
        ev += [(at, "note", g, m) for at, m, g in fun.relax_events(r)]
    elif t == "wyr":
        ev += [(0.15, "whoosh", 0.3), (0.8, "pop", 0.4), (1.1, "whoosh", 0.3), (3.2, "pop", 0.3)]
    elif t == "month":
        ev += [(0.25 + 0.16 * i, "note", 0.12, 72 + [0, 2, 4, 7, 9][i % 5] + 12 * (i // 5)) for i in range(12)]
        ev += [(2.8, "pop", 0.3)]
    elif t == "hack":
        for row, rw in enumerate(r["rows"]):
            t0 = rw[2] if len(rw) > 2 else 1.2 + 1.4 * row
            ev += [(t0 + 0.08 * k, "click", 0.35) for k in range(len(rw[1]))]
        ev += [(5.2, "pop", 0.3)]
    return ev


# ---------------- mixdown ----------------
def soundtrack(r, seed, out_wav):
    rng = np.random.default_rng(seed)
    # each format gets its own signature sound (the key still varies per reel)
    style = {"riddle": "mallet", "quiz": "bounce", "fact": "lofi", "maths": "mallet",
             "stroop": "bounce", "hack": "lofi", "relax": "ambient", "wyr": "bounce", "month": "mallet"}.get(r["type"], STYLES[seed % len(STYLES)])
    root = 60 + [0, 2, 5, 7, -3][seed % 5]            # C, D, F, G, A
    bed = music(style, root, rng)
    # duck the music while the countdown ticks, so the ticks read clearly
    duck = np.ones(N)
    if r["type"] in ("riddle", "quiz"):
        tt = _t(N)
        duck = np.where((tt > 1.3) & (tt < 5.4), 0.6, 1.0)
        duck = np.convolve(duck, np.ones(2000) / 2000, mode="same")
    mix = bed * duck[:, None] * 0.8
    fx = np.zeros((N, 2))
    for e in events_for(r):
        at, name, g = e[0], e[1], e[2]
        sig = {"tick": sfx_tick, "bell": sfx_bell, "correct": sfx_correct, "pop": sfx_pop,
               "boom": sfx_boom}.get(name)
        if sig: s = sig()
        elif name == "whoosh": s = sfx_whoosh(rng)
        elif name == "blip": s = sfx_blip(e[3] if len(e) > 3 else 0)
        elif name == "click": s = sfx_click(rng)
        elif name == "note": s = sfx_note(e[3])
        else: continue
        _place(fx, s, at, g)
    mix = mix + fx
    # fade the loop edges a touch, normalise loudness, soft-limit
    f = int(0.02 * SR)
    mix[:f] *= np.linspace(0, 1, f)[:, None]; mix[-f:] *= np.linspace(1, 0, f)[:, None]
    rms = np.sqrt(np.mean(mix ** 2)) + 1e-9
    target = {"relax": -21, "month": -18}.get(r["type"], -16)   # calm formats sit quieter
    mix *= 10 ** (target / 20) / rms
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)           # gentle limiter, peaks < 0 dBFS
    peak = np.max(np.abs(mix))
    if peak > 0.89: mix *= 0.89 / peak                # keep peaks under -1 dBFS
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return style
