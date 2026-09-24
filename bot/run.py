"""Riddle Crumbs posting robot.

  python bot/run.py prepare --event schedule --cron "0 18 * * *"   # decide + render into site/
  python bot/run.py publish --base https://<user>.github.io/<repo>/  # post the rendered reel
  python bot/run.py check                                          # verify the Instagram token

State lives in state/state.json (committed back by the workflow). The Instagram token is
the IG_TOKEN repository secret; refreshed tokens are stored encrypted in state/token.enc,
using a key derived from IG_TOKEN, so only this repo's workflow can read them.
"""
import argparse, base64, datetime as dt, hashlib, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bot"))
import content  # noqa: E402

STATE = ROOT / "state" / "state.json"
TOKEN_ENC = ROOT / "state" / "token.enc"
SITE = ROOT / "site"
PENDING = ROOT / "pending.json"
API = "https://graph.instagram.com/v23.0"
SLOTS = {"0 7 * * *": 0, "0 12 * * *": 1, "0 18 * * *": 2}   # UTC: 8am / 1pm / 7pm UK summer time
MOCK = os.environ.get("MOCK_API") == "1"


# ---------------- helpers ----------------
def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"next": 0, "start": None, "paused": False, "last_slot": None, "token_refreshed": None, "log": []}


def save_state(s):
    STATE.parent.mkdir(exist_ok=True)
    s["log"] = s["log"][-200:]
    STATE.write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n")


def gh_output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    lines = [f"{k}={v}" for k, v in kv.items()]
    if path:
        with open(path, "a") as f: f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def today():
    return dt.datetime.now(dt.timezone.utc).date()


def allowed_slots(day_index):
    """Ramp-up: week 1 -> 1/day, week 2 -> 2/day, then 3/day."""
    if day_index < 7: return {2}
    if day_index < 14: return {1, 2}
    return {0, 1, 2}


# ---------------- token handling ----------------
def _fernet():
    from cryptography.fernet import Fernet
    secret = os.environ["IG_TOKEN"].strip()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))


def mask(tok):
    if os.environ.get("GITHUB_ACTIONS"): print(f"::add-mask::{tok}")


def api(method, path, **params):
    if MOCK:
        return mock_api(method, path, params)
    import requests
    url = path if path.startswith("http") else f"{API}/{path}"
    r = requests.request(method, url, params=params if method == "GET" else None,
                         data=params if method != "GET" else None, timeout=60)
    try: body = r.json()
    except Exception: body = {"raw": r.text[:300]}
    if r.status_code >= 400 or "error" in body:
        err = body.get("error", body)
        raise RuntimeError(f"Instagram API error on {path.split('?')[0]}: {json.dumps(err)[:500]}")
    return body


def candidate_tokens():
    secret = os.environ.get("IG_TOKEN", "").strip()
    if not secret:
        raise SystemExit("IG_TOKEN secret is missing. Add it in Settings > Secrets and variables > Actions.")
    toks = []
    if TOKEN_ENC.exists():
        try:
            toks.append(_fernet().decrypt(TOKEN_ENC.read_bytes()).decode())
        except Exception:
            print("Stored refreshed token can't be read with the current IG_TOKEN (secret was changed?) - using the secret.")
    toks.append(secret)
    for t in toks: mask(t)
    return toks


def get_token_and_user():
    last = None
    for tok in candidate_tokens():
        try:
            me = api("GET", "me", fields="user_id,username", access_token=tok)
            return tok, me
        except Exception as e:
            last = e
    raise SystemExit(f"No working Instagram token. It has probably expired - generate a new one in the Meta "
                     f"dashboard and update the IG_TOKEN secret. Details: {last}")


def maybe_refresh(tok, state):
    last = state.get("token_refreshed")
    if last and (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(last)).days < 7:
        return
    try:
        new = api("GET", "https://graph.instagram.com/refresh_access_token",
                  grant_type="ig_refresh_token", access_token=tok)["access_token"]
        mask(new)
        TOKEN_ENC.write_bytes(_fernet().encrypt(new.encode()))
        state["token_refreshed"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        print("Token refreshed (valid for another ~60 days).")
    except Exception as e:
        print(f"Token refresh skipped: {e}")


# ---------------- commands ----------------
def cmd_prepare(a):
    s = load_state()
    go, publish, why = False, False, ""
    if a.event == "workflow_dispatch":
        go, publish = True, a.mode == "post"
        why = f"manual run ({a.mode})"
    elif a.event == "schedule":
        slot = SLOTS.get(a.cron.strip())
        start = dt.date.fromisoformat(s["start"]) if s["start"] else today()
        day = (today() - start).days
        key = f"{today().isoformat()}-{slot}"
        if s.get("paused"): why = "paused in state.json"
        elif slot is None: why = f"unknown schedule {a.cron!r}"
        elif s.get("last_slot") == key: why = "this slot already posted"
        elif slot not in allowed_slots(day): why = f"ramp-up day {day}: slot {slot} not used yet"
        else: go, publish, why = True, True, f"day {day}, slot {slot}"
    print("Decision:", why)
    if not go:
        gh_output(go="false", publish="false"); return

    n = s["next"]
    it = content.item_for(n)
    import engine
    SITE.mkdir(exist_ok=True)
    fname = f"r{n:04d}-{it['id']}.mp4"
    t0 = time.time()
    engine.render(it, SITE / fname)
    print(f"Rendered post #{n}: {it['type']} / {it['id']} in {time.time() - t0:.0f}s")
    (SITE / ".nojekyll").write_text("")
    (SITE / "index.html").write_text("<!doctype html><title>Riddle Crumbs</title><p>Nothing to see here.</p>")
    cover_ms = {"quiz": 2500, "maths": 2600, "fact": 3200, "stroop": 2500, "hack": 3000}.get(it["type"], 0)
    PENDING.write_text(json.dumps({"n": n, "id": it["id"], "type": it["type"], "file": fname,
                                   "caption": content.caption(it), "thumb_offset": cover_ms,
                                   "slot": f"{today().isoformat()}-{SLOTS.get(a.cron.strip())}" if a.event == "schedule" else None},
                                  ensure_ascii=False, indent=1))
    left = content.stock_left(n + 1)
    print("Hand-written stock left after this post:", left)
    gh_output(go="true", publish="true" if publish else "false", file=fname)


def wait_public(url, timeout=300):
    if MOCK: return
    import requests
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.head(url, timeout=20, allow_redirects=True)
            if r.status_code == 200: return
        except Exception: pass
        time.sleep(10)
    raise SystemExit(f"Video never became public at {url}")


def cmd_publish(a):
    s = load_state()
    p = json.loads(PENDING.read_text())
    tok, me = get_token_and_user()
    uid = me["user_id"]
    print(f"Posting to @{me.get('username')} - post #{p['n']} ({p['type']}: {p['id']})")
    url = a.base.rstrip("/") + "/" + p["file"]
    wait_public(url)
    params = dict(media_type="REELS", video_url=url, caption=p["caption"], share_to_feed="true", access_token=tok)
    if p["thumb_offset"]: params["thumb_offset"] = str(p["thumb_offset"])
    cid = api("POST", f"{uid}/media", **params)["id"]
    for _ in range(60):  # up to ~10 min of processing
        st = api("GET", cid, fields="status_code,status", access_token=tok)
        code = st.get("status_code")
        if code == "FINISHED": break
        if code in ("ERROR", "EXPIRED"): raise SystemExit(f"Instagram couldn't process the video: {st}")
        time.sleep(10)
    else:
        raise SystemExit("Timed out waiting for Instagram to process the video.")
    media = api("POST", f"{uid}/media_publish", creation_id=cid, access_token=tok)["id"]
    print(f"Published! media id {media}")
    s["next"] = p["n"] + 1
    if not s["start"]: s["start"] = today().isoformat()
    if p.get("slot"): s["last_slot"] = p["slot"]
    s["log"].append({"n": p["n"], "id": p["id"], "media": media,
                     "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")})
    maybe_refresh(tok, s)
    save_state(s)


def cmd_check(a):
    tok, me = get_token_and_user()
    print(f"Token works. Connected to @{me.get('username')} (id {me.get('user_id')}).")
    s = load_state()
    print(f"Next post number: {s['next']}. Hand-written stock left:", content.stock_left(s["next"]))


# ---------------- local testing ----------------
_mock = {"polls": 0}
def mock_api(method, path, params):
    print(f"[mock] {method} {path.split('?')[0]} {sorted(k for k in params if k != 'access_token')}")
    if path == "me": return {"user_id": "17841426069748577", "username": "riddlecrumbs"}
    if path.endswith("/media"): return {"id": "C123"}
    if path == "C123":
        _mock["polls"] += 1
        return {"status_code": "FINISHED" if _mock["polls"] > 1 else "IN_PROGRESS"}
    if path.endswith("/media_publish"): return {"id": "M999"}
    if "refresh_access_token" in path: return {"access_token": "NEWTOKEN123", "expires_in": 5184000}
    raise RuntimeError("unmocked " + path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("prepare"); p1.add_argument("--event", default="workflow_dispatch")
    p1.add_argument("--mode", default="test"); p1.add_argument("--cron", default="")
    p2 = sub.add_parser("publish"); p2.add_argument("--base", required=True)
    sub.add_parser("check")
    a = ap.parse_args()
    {"prepare": cmd_prepare, "publish": cmd_publish, "check": cmd_check}[a.cmd](a)
