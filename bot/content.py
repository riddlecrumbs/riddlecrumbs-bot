"""What to post next - with a hard rule: nothing is ever posted twice.

Every reel has a "key" (the idea behind it: a riddle, a trick, an animation concept...). The robot keeps a list
of used keys in state.json and always picks the next unused item. If a stream runs out, it borrows from another
stream; if everything is used up, it skips the slot rather than repeat anything. New content = refill the banks.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_bank(): return json.loads((ROOT / "content" / "bank.json").read_text())
def load_fun(): return json.loads((ROOT / "content" / "fun.json").read_text())


# ---------------------------------------------------------------- maths tricks (each trick used once)
def _steps(a, b, c, d):
    return [[0.0, a[0], a[1]], [2.2, b[0], b[1]], [3.6, c[0], c[1]], [5.0, d[0], d[1]]]


def maths_tricks():
    T = []
    def add(key, q, steps, cap, answer_check):
        assert answer_check, key
        T.append({"id": key, "key": key, "type": "maths", "q": q, "steps": steps, "cap": cap})
    add("trick_x11", "Times *11* in your head. Instantly.", _steps(("36 × 11", ""), ("3  □  6", "Split the digits"), ("3 (3+6) 6", "Add them, put it in the middle"), ("396", "Done!")),
        "Two-digit number × 11: split the digits and put their sum in the middle. 36 × 11 → 3 (9) 6 = 396.", 36 * 11 == 396)
    add("trick_x5", "Times *5* without a calculator.", _steps(("68 × 5", ""), ("68 ÷ 2 = 34", "Halve it"), ("34 → 340", "Stick a zero on the end"), ("340", "Done!")),
        "×5 is the same as ×10 then ÷2. So halve it and add a zero: 68 → 34 → 340. Odd number? 37 → 18.5 → 185.", 68 * 5 == 340)
    add("trick_sq5", "Square numbers ending in *5.* Instantly.", _steps(("65²", ""), ("6 × 7 = 42", "First digit × the next number"), ("42 | 25", "Put 25 on the end"), ("4225", "Done!")),
        "Any number ending in 5: multiply the first digit by the next number up, then write 25 after it. 65² → 6×7 = 42 → 4225.", 65 ** 2 == 4225)
    add("trick_x25", "Times *25* in your head.", _steps(("48 × 25", ""), ("48 ÷ 4 = 12", "Divide by 4"), ("12 → 1200", "Add two zeros"), ("1200", "Done!")),
        "25 is 100 ÷ 4. So divide by 4 and add two zeros: 48 → 12 → 1200. Like counting quarters in pounds.", 48 * 25 == 1200)
    add("trick_x9", "Times *9* the easy way.", _steps(("47 × 9", ""), ("47 × 10 = 470", "Times 10 first"), ("470 − 47", "Then take one 47 away"), ("423", "Done!")),
        "×9 is ×10 minus one lot of the number. 47 × 9 → 470 − 47 = 423.", 47 * 9 == 423)
    add("trick_x99", "Times *99* in seconds.", _steps(("34 × 99", ""), ("34 × 100 = 3400", "Times 100 first"), ("3400 − 34", "Take one 34 away"), ("3366", "Done!")),
        "×99 is ×100 minus the number once. 34 × 99 → 3400 − 34 = 3366.", 34 * 99 == 3366)
    add("trick_x101", "Times *101*? Just write it twice.", _steps(("47 × 101", ""), ("47 | 47", "Write the number twice"), ("4747", "That's it"), ("4747", "Done!")),
        "Any two-digit number × 101 is just that number written twice: 47 × 101 = 4747, 83 × 101 = 8383.", 47 * 101 == 4747)
    add("trick_x4", "Times *4*? Double, then double.", _steps(("37 × 4", ""), ("37 → 74", "Double it"), ("74 → 148", "Double it again"), ("148", "Done!")),
        "×4 is just doubling twice. 37 → 74 → 148. Works for ×8 too: double three times.", 37 * 4 == 148)
    add("trick_div5", "Divide by *5* in your head.", _steps(("140 ÷ 5", ""), ("140 × 2 = 280", "Double it"), ("280 ÷ 10", "Move the decimal one place"), ("28", "Done!")),
        "÷5 is the same as ×2 then ÷10. 140 → 280 → 28.", 140 / 5 == 28)
    add("trick_percent", "*8% of 50?* Flip it.", _steps(("8% of 50", ""), ("= 50% of 8", "Swap the numbers"), ("half of 8", "Much easier"), ("4", "Done!")),
        "x% of y is always the same as y% of x. So 8% of 50 = 50% of 8 = 4. Try it with 4% of 75!", 0.08 * 50 == 4)
    add("trick_x15", "Times *15* in your head.", _steps(("24 × 15", ""), ("24 + 12 = 36", "Add half of it"), ("36 × 10", "Then times 10"), ("360", "Done!")),
        "×15 = ×10 plus half again. 24 → 24 + 12 = 36 → 360.", 24 * 15 == 360)
    add("trick_near100", "Multiply numbers *near 100.*", _steps(("97 × 96", ""), ("−3   and   −4", "How far below 100?"), ("96−3 = 93 | 3×4 = 12", "Cross-subtract | multiply gaps"), ("9312", "Done!")),
        "For numbers just under 100: subtract one gap from the other number, then multiply the gaps. 97 × 96 → 93 | 12 → 9312.", 97 * 96 == 9312)
    add("trick_x12", "Times *12* without a calculator.", _steps(("23 × 12", ""), ("23 × 10 = 230", "Times 10"), ("23 × 2 = 46", "Times 2"), ("276", "Add them: done!")),
        "×12 = ×10 + ×2. 23 × 12 → 230 + 46 = 276.", 23 * 12 == 276)
    add("trick_sq50", "Square numbers *near 50.*", _steps(("48²", ""), ("25 − 2 = 23", "25 minus the gap from 50"), ("23 | 2² = 04", "Then square the gap"), ("2304", "Done!")),
        "For numbers near 50: start from 25, adjust by the gap, then add the gap squared as two digits. 48² → 23 | 04 → 2304.", 48 ** 2 == 2304)
    add("trick_div3", "Is it divisible by *3?*", _steps(("4,572 ÷ 3?", ""), ("4+5+7+2 = 18", "Add up the digits"), ("18 ÷ 3 = 6", "Is that divisible by 3?"), ("Yes!", "Then the big number is too")),
        "A number divides by 3 exactly when its digits add up to a multiple of 3. 4,572 → 18 → yes (4,572 ÷ 3 = 1,524).", 4572 % 3 == 0)
    add("trick_tip15", "Work out a *15% tip* fast.", _steps(("15% of £46", ""), ("10% = £4.60", "Move the decimal"), ("5% = £2.30", "Half of that"), ("£6.90", "Add them: done!")),
        "15% = 10% + 5%. 10% of £46 is £4.60, half of that is £2.30, together £6.90.", abs(46 * 0.15 - 6.90) < 1e-9)
    return T


# ---------------------------------------------------------------- brain tests (each used once)
def brain_tests():
    return [
        {"id": "test_countf", "key": "test_countf", "type": "test", "kind": "countf",
         "q": "Count the *F's* in this sentence.",
         "text": "FINISHED FILES ARE THE RESULT OF YEARS OF SCIENTIFIC STUDY COMBINED WITH THE EXPERIENCE OF YEARS",
         "answer": "There are 6!",
         "cap": "Most people count 3. Your brain skims over the F in \"of\" because it sounds like a V. Did you get 6?",
         "tags": "#braintest #puzzle #brain #mindgames #challenge"},
        {"id": "test_thethe", "key": "test_thethe", "type": "test", "kind": "thethe",
         "q": "Read the sign out loud.",
         "answer": "Look again: \"THE\" is there twice!",
         "cap": "Your brain predicts familiar phrases and skips the repeated word. Did you spot it first time?",
         "tags": "#braintest #illusion #brain #mindgames #didyouknow"},
        {"id": "test_lines", "key": "test_lines", "type": "test", "kind": "lines",
         "q": "Which line is *longer?*",
         "answer": "They're exactly the same length!",
         "cap": "This is the Müller-Lyer illusion: the arrow ends trick your brain into misjudging length. Did it fool you?",
         "tags": "#opticalillusion #illusion #brain #mindblown #braintest"},
        {"id": "test_circles", "key": "test_circles", "type": "test", "kind": "circles",
         "q": "Which *orange circle* is bigger?",
         "answer": "They're exactly the same size!",
         "cap": "This is the Ebbinghaus illusion: the circles around them change how big they look. Which one did you pick?",
         "tags": "#opticalillusion #illusion #brain #mindblown #braintest"},
        {"id": "test_scramble", "key": "test_scramble", "type": "test", "kind": "scramble",
         "q": "Can you read this?",
         "text": "Yuor barin is so cevler it can raed tihs eevn wehn the lterets are all mexid up.",
         "answer": "Your brain reads whole words, not letters.",
         "cap": "As long as the first and last letters stay put, most people can read scrambled words surprisingly easily. Could you?",
         "tags": "#braintest #brain #mindblown #canyouread #challenge"},
    ]


# ---------------------------------------------------------------- satisfying concepts (each used once)
FUN_CONCEPTS = {  # the five drawn in fun.py
    "orbits": ("Try to look away.", "sunset"), "ripple": ("Your brain needs this.", "neon"),
    "lissajous": ("Can't stop watching.", "candy"), "squares": ("This is so smooth.", "aurora"),
    "flower": ("Just breathe.", "brand"),
}
RELAX_ORDER = ["orbits", "newton", "galton", "flower", "gears", "sand", "lissajous", "maze", "fireworks", "ripple",
               "dominoes", "tree", "packing", "corner", "hilbert", "squares", "lava", "stringart", "cells", "globe",
               "bubbles", "kaleido", "paint", "blocks", "ripples", "assemble"]
RETIRED_RELAX = {"pendulum", "circle", "sort", "spiro"}   # already posted - never used again


def relax_library():
    import loops
    out = []
    for i, key in enumerate(RELAX_ORDER):
        hook, pal = FUN_CONCEPTS.get(key) or (loops.CONCEPTS[key]["hook"], loops.CONCEPTS[key]["pal"])
        out.append({"id": f"x_{key}", "key": f"relax_{key}", "type": "relax", "variant": key, "seed": 9000 + i,
                    "hook": hook, "pal": pal})
    return out


# ---------------------------------------------------------------- libraries per stream
BRAIN_PATTERN = ["riddle", "quiz", "fact", "maths", "riddle", "hack", "test", "quiz", "riddle", "fact"]


def brain_pools():
    bank = load_bank()
    pools = {f: [dict(it, type=f, key=it["id"]) for it in bank.get(f, [])] for f in ("riddle", "quiz", "fact", "hack")}
    pools["maths"] = maths_tricks()
    pools["test"] = brain_tests()
    return pools


def social_pools():
    fun = load_fun()
    return {f: [dict(it, type=f, key=it["id"]) for it in fun[f]] for f in ("wyr", "month")}


SOCIAL_PATTERN = ["wyr", "month", "wyr"]


def _pick_patterned(pools, pattern, used, turn):
    """Follow the format pattern from position `turn`; take the first unused item of that format,
    moving on through the pattern if a format has run dry."""
    for step in range(len(pattern)):
        fmt = pattern[(turn + step) % len(pattern)]
        for it in pools.get(fmt, []):
            if it["key"] not in used: return it
    return None


def pick(stream, used, turns):
    """Next never-posted item for a stream (turns = how many posts that stream has made)."""
    if stream == "relax":
        for it in relax_library():
            if it["key"] not in used: return it
        return None
    if stream == "social":
        return _pick_patterned(social_pools(), SOCIAL_PATTERN, used, turns)
    return _pick_patterned(brain_pools(), BRAIN_PATTERN, used, turns)


def next_item(stream, used, turns):
    """Own stream first; if it's empty, borrow from the others; None if absolutely everything is used."""
    order = [stream] + [s for s in ("relax", "brain", "social") if s != stream]
    for s in order:
        it = pick(s, used, turns.get(s, 0))
        if it: return s, it
    return None, None


def stock(used):
    """Unused items left per stream."""
    rl = sum(1 for it in relax_library() if it["key"] not in used)
    br = sum(1 for p in brain_pools().values() for it in p if it["key"] not in used)
    so = sum(1 for p in social_pools().values() for it in p if it["key"] not in used)
    return {"relax": rl, "brain": br, "social": so}


# keys of everything posted before this system existed (from the robot's log)
LEGACY_KEYS = {
    "r_footsteps": "r_footsteps", "q_venus": "q_venus", "f_octopus": "f_octopus", "m_x11_36": "trick_x11",
    "r_towel": "r_towel", "h_reopen_tab": "h_reopen_tab", "s_0": "test_stroop",
}


def legacy_key(log_id):
    if log_id.startswith("x_"):
        v = log_id.split("_")[1]
        return f"relax_{v}"
    return LEGACY_KEYS.get(log_id, log_id)


# ---------------------------------------------------------------- captions
TAGS = {
    "riddle": "#riddles #brainteaser #riddle #puzzle #thinkfast",
    "quiz": "#quiz #trivia #didyouknow #brainteaser #learnsomethingnew",
    "fact": "#didyouknow #funfacts #mindblown #learnsomethingnew #science",
    "maths": "#mathtricks #maths #mentalmath #mathhacks #learnsomethingnew",
    "hack": "#lifehacks #techtips #computertips #productivity #shortcuts",
}


def caption(it):
    t = it["type"]
    if t in ("relax", "wyr", "month"): return fun_caption(it)
    if t == "test": return f"{it['cap']}\n\nFollow @riddlecrumbs for a daily brain snack \U0001F36A\n\n{it['tags']}"
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
        body = it.get("cap", "")
    return f"{body}\n\n{tags}"


def fun_caption(it):
    t = it["type"]
    if t == "relax":
        return ("Could you watch this all day? \U0001F60C\n\nFollow @riddlecrumbs for a daily brain snack \U0001F36A\n\n"
                "#oddlysatisfying #satisfying #relaxing #calm #mesmerizing")
    if t == "wyr":
        return (f"Would you rather... {it['a'].lower()} {it['ea']} or {it['b'].lower()} {it['eb']}?\n\n"
                "Comment A or B \U0001F447 and tag someone who'd pick the other one!\n\n"
                "#wouldyourather #thisorthat #funquestions #chooseone #tagafriend")
    return (f"What's your {it['what']}? Comment your month \U0001F447 and tag a friend to find theirs!\n\n"
            "#birthmonth #whatsyours #funquiz #tagafriend #justforfun")
