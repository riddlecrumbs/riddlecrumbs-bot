"""Builds the posting queue: hand-written items from content/bank.json interleaved by format,
plus procedurally generated maths tricks and brain tests that never run out.

Post number n (0-based) always maps to the same reel, so the queue is deterministic and
state only needs to remember n."""
import json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERN = ["riddle", "quiz", "fact", "maths", "riddle", "hack", "stroop", "quiz", "riddle", "fact"]
FALLBACK = {"riddle": "maths", "quiz": "stroop", "fact": "maths", "hack": "stroop"}


def load_bank():
    return json.loads((ROOT / "content" / "bank.json").read_text())


# ---------- procedural formats (answers computed, so always correct) ----------
def _pool(kind):
    if kind == "x11": vals = [10 * a + b for a in range(1, 10) for b in range(1, 10) if a + b <= 9]
    elif kind == "x5": vals = list(range(24, 98, 2))
    elif kind == "sq5": vals = [10 * a + 5 for a in range(2, 12)]
    else: vals = list(range(12, 96, 4))
    random.Random(kind).shuffle(vals)
    return vals


def maths_item(k):
    kinds = ["x11", "x5", "sq5", "x11", "x25"]
    kind = kinds[k % 5]
    # the j-th time this kind comes up -> the j-th number from a fixed shuffled pool (no repeats until it's used up)
    j = sum(1 for i in range(k) if kinds[i % 5] == kind)
    pool = _pool(kind)
    n = pool[j % len(pool)]
    if kind == "x11":
        a, b = divmod(n, 10)
        steps = [[0.0, f"{n} × 11", ""], [2.2, f"{a}  □  {b}", "Split the digits"],
                 [3.6, f"{a} ({a}+{b}) {b}", "Add them, put it in the middle"], [5.0, f"{n * 11}", "Done!"]]
        return {"id": f"m_x11_{n}", "type": "maths", "q": "Times *11* in your head. Instantly.", "steps": steps,
                "cap": f"Two-digit number × 11: split the digits and put their sum in the middle. {n} × 11 → {a} ({a + b}) {b} = {n * 11}.\n"
                       "If the middle adds up to 10 or more, carry the 1: 58 × 11 → 5 (13) 8 → 638."}
    if kind == "x5":
        steps = [[0.0, f"{n} × 5", ""], [2.2, f"{n} ÷ 2 = {n // 2}", "Halve it"],
                 [3.6, f"{n // 2} → {n // 2}0", "Stick a zero on the end"], [5.0, f"{n * 5}", "Done!"]]
        return {"id": f"m_x5_{n}", "type": "maths", "q": "Times *5* without a calculator.", "steps": steps,
                "cap": f"×5 is the same as ×10 then ÷2. So halve it and add a zero: {n} → {n // 2} → {n * 5}.\n"
                       "Odd number? Halve it to get a .5, e.g. 37 → 18.5 → 185."}
    if kind == "sq5":
        a = n // 10
        steps = [[0.0, f"{n}²", ""], [2.2, f"{a} × {a + 1} = {a * (a + 1)}", "First digit × the next number"],
                 [3.6, f"{a * (a + 1)} | 25", "Put 25 on the end"], [5.0, f"{n * n}", "Done!"]]
        return {"id": f"m_sq5_{n}", "type": "maths", "q": "Square numbers ending in *5.* Instantly.", "steps": steps,
                "cap": f"For any number ending in 5: multiply the first digit by the next number up, then write 25 after it. {n}² → {a}×{a + 1} = {a * (a + 1)} → {n * n}."}
    # x25
    steps = [[0.0, f"{n} × 25", ""], [2.2, f"{n} ÷ 4 = {n // 4}", "Divide by 4"],
             [3.6, f"{n // 4} → {n // 4}00", "Add two zeros"], [5.0, f"{n * 25}", "Done!"]]
    return {"id": f"m_x25_{n}", "type": "maths", "q": "Times *25* in your head.", "steps": steps,
            "cap": f"25 is 100 ÷ 4. So divide by 4 and add two zeros: {n} → {n // 4} → {n * 25}. Think of it as counting quarters in pounds."}


STROOP_COLOURS = {"RED": (255, 92, 92), "BLUE": (92, 172, 255), "GREEN": (80, 222, 124),
                  "YELLOW": (255, 212, 64), "PINK": (255, 128, 200), "ORANGE": (255, 150, 60)}


def stroop_item(k):
    rnd = random.Random(5000 + k)
    names = list(STROOP_COLOURS)
    ws = names[:]; rnd.shuffle(ws)            # each colour word appears once
    while True:                               # colours: a shuffle where no word gets its own colour
        cs = names[:]; rnd.shuffle(cs)
        if all(a != b for a, b in zip(ws, cs)): break
    words = [[w, list(STROOP_COLOURS[c])] for w, c in zip(ws, cs)]
    return {"id": f"s_{k}", "type": "stroop", "words": words,
            "cap": "This is the Stroop effect: your brain reads words automatically, so naming the colour means fighting your own reflex. How fast did you get through it?",
            "tags": "#braintest #psychology #brain #mindgames #challenge"}


# ---------- queue ----------
def _plan(n, bank):
    """Effective format for each post 0..n (hand-written format, or its fallback once stock runs out),
    and how many times that effective format was used before."""
    used = {f: 0 for f in PATTERN}
    eff_count = {}
    plan = []
    for i in range(n + 1):
        fmt = PATTERN[i % len(PATTERN)]
        if fmt in ("maths", "stroop") or used[fmt] < len(bank.get(fmt, [])):
            eff = fmt
            k = used[fmt] if fmt not in ("maths", "stroop") else eff_count.get(fmt, 0)
        else:
            eff = FALLBACK[fmt]
            k = eff_count.get(eff, 0)
        if fmt not in ("maths", "stroop"): used[fmt] += 1
        if eff in ("maths", "stroop"): eff_count[eff] = eff_count.get(eff, 0) + 1
        plan.append((fmt, eff, k))
    return plan


def item_for(n):
    """The reel for post number n."""
    bank = load_bank()
    fmt, eff, k = _plan(n, bank)[n]
    if eff == "maths": return maths_item(k)
    if eff == "stroop": return stroop_item(k)
    it = dict(bank[fmt][k]); it["type"] = fmt
    return it


def stock_left(n):
    """How many hand-written posts remain from post n onward, per format."""
    bank = load_bank()
    out = {}
    for fmt in ("riddle", "quiz", "fact", "hack"):
        used = sum(1 for i in range(n) if PATTERN[i % len(PATTERN)] == fmt)
        out[fmt] = max(0, len(bank.get(fmt, [])) - used)
    return out


TAGS = {
    "riddle": "#riddles #brainteaser #riddle #puzzle #thinkfast",
    "quiz": "#quiz #trivia #didyouknow #brainteaser #learnsomethingnew",
    "fact": "#didyouknow #funfacts #mindblown #learnsomethingnew #science",
    "maths": "#mathtricks #maths #mentalmath #mathhacks #learnsomethingnew",
    "stroop": "#braintest #psychology #brain #mindgames #challenge",
    "hack": "#lifehacks #techtips #computertips #productivity #shortcuts",
}


def caption(it):
    t = it["type"]
    if t in ("relax", "wyr", "month"): return fun_caption(it)
    tags = it.get("tags", TAGS[t])
    if t == "riddle":
        body = ("Think you've got it? Drop your answer below \U0001F447 No peeking!\n.\n.\n.\n.\n"
                f"Answer: {it['a']} \U0001F36A")
    elif t == "quiz":
        body = f"{it.get('cap', '')}\n\nDid you get it right? Tell me in the comments \U0001F447".strip()
    elif t == "fact":
        body = f"{it.get('cap', '')}\n\nFollow @riddlecrumbs for a daily brain snack \U0001F36A".strip()
    elif t == "maths":
        body = f"{it['cap']}\n\nSave it and try it on someone \U0001F60F"
    elif t == "hack":
        body = f"{it.get('cap', '')}\n\nSend this to someone who needs it \U0001F4BB".strip()
    else:
        body = it["cap"]
    return f"{body}\n\n{tags}"


if __name__ == "__main__":
    for n in range(12):
        it = item_for(n)
        print(n, it["type"], it["id"])
    print(stock_left(0))


# ---------- zero-effort streams ----------
RELAX_VARIANTS = ["pendulum", "circle", "sort", "spiro"]
RELAX_HOOKS = ["Try to look away.", "Watch it loop.", "So satisfying...", "Your brain needs this.", "Just breathe."]


def relax_item(k):
    return {"id": f"x_{RELAX_VARIANTS[k % 4]}_{k}", "type": "relax", "variant": RELAX_VARIANTS[k % 4],
            "seed": 7000 + k, "hook": RELAX_HOOKS[k % len(RELAX_HOOKS)]}


def load_fun():
    return json.loads((ROOT / "content" / "fun.json").read_text())


SOCIAL_PATTERN = ["wyr", "month", "wyr"]


def social_item(k):
    fun = load_fun()
    fmt = SOCIAL_PATTERN[k % len(SOCIAL_PATTERN)]
    j = sum(1 for i in range(k) if SOCIAL_PATTERN[i % len(SOCIAL_PATTERN)] == fmt)
    items = fun[fmt]
    it = dict(items[j % len(items)]); it["type"] = fmt
    if j >= len(items): it["id"] += f"_r{j // len(items)}"   # repeats only after the whole bank is used
    return it


def stream_item(stream, k):
    if stream == "relax": return relax_item(k)
    if stream == "social": return social_item(k)
    return item_for(k)


def fun_caption(it):
    t = it["type"]
    if t == "relax":
        return ("Could you watch this all day? \U0001F60C\n\nFollow @riddlecrumbs for a daily brain snack \U0001F36A\n\n"
                "#oddlysatisfying #satisfying #relaxing #loop #calm")
    if t == "wyr":
        return (f"Would you rather... {it['a'].lower()} {it['ea']} or {it['b'].lower()} {it['eb']}?\n\n"
                "Comment A or B \U0001F447 and tag someone who'd pick the other one!\n\n"
                "#wouldyourather #thisorthat #funquestions #chooseone #tagafriend")
    return (f"What's your {it['what']}? Comment your month \U0001F447 and tag a friend to find theirs!\n\n"
            "#birthmonth #whatsyours #funquiz #tagafriend #justforfun")
