#!/usr/bin/env python3
"""
Agosto Studio - on-demand poster.

Posts the next N unused items from content_queue.json to Instagram, Facebook,
and TikTok, then marks them used so the next run picks up where you left off.

USAGE
  python3 agosto_run.py                # post the next 2 items (per platform)
  python3 agosto_run.py --count 3      # post the next 3
  python3 agosto_run.py --schedule "2026-07-02T10:00"   # schedule instead of now
  python3 agosto_run.py --dry-run      # show what would post, send nothing

The API key is read from the local file ".zernio_key" (created for you).
Or pass it explicitly:  python3 agosto_run.py --key sk_xxx
"""
import os, sys, json, time, argparse, mimetypes
import urllib.request, urllib.error

BASE = "https://zernio.com/api/v1"
TIMEZONE = "America/New_York"
HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, "media")
QUEUE = os.path.join(HERE, "content_queue.json")
KEYFILE = os.path.join(HERE, ".zernio_key")

FB = {"platform": "facebook",  "accountId": "6a40373e9d9472faae08d5fd"}
IG = {"platform": "instagram", "accountId": "6a4036e09d9472faae08d2b8"}
TT = {"platform": "tiktok",    "accountId": "6a4036c39d9472faae08d1c4"}


def api(method, path, key, body=None, raw=None, ctype=None, full_url=None):
    url = full_url or (BASE + path)
    headers = {}
    if key:
        headers["Authorization"] = "Bearer " + key
    data = None
    if body is not None:
        data = json.dumps(body).encode(); headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw; headers["Content-Type"] = ctype or "application/octet-stream"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            t = r.read().decode()
            return r.status, (json.loads(t) if t.strip().startswith(("{", "[")) else t)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def fetch_bytes(url):
    """Download a remote image (used for stock-photo posts)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ctype = r.headers.get("Content-Type", "").split(";")[0] or "image/jpeg"
        return r.read(), ctype


def resolve_image(item):
    """Return (filename, bytes, content_type) from a local file or a remote URL."""
    if item.get("img_url"):
        data, ctype = fetch_bytes(item["img_url"])
        ext = ".jpg" if "jpeg" in ctype or "jpg" in ctype else ".png"
        return item["id"] + ext, data, (ctype if ctype.startswith("image/") else "image/jpeg")
    path = os.path.join(MEDIA, item["img"])
    with open(path, "rb") as f:
        return os.path.basename(path), f.read(), (mimetypes.guess_type(path)[0] or "image/png")


def upload(item, key, dry):
    if dry:
        return "https://DRY/" + item["id"]
    fname, raw, ctype = resolve_image(item)
    st, j = api("POST", "/media", key, body={"filename": fname, "contentType": ctype})
    if st != 200 or not isinstance(j, dict):
        raise RuntimeError(f"presign failed ({st}): {j}")
    pst, _ = api("PUT", None, None, raw=raw, ctype=ctype, full_url=j["uploadUrl"])
    if pst not in (200, 201, 204):
        raise RuntimeError(f"PUT failed ({pst})")
    return j["publicUrl"]


def make_body(content, accounts, media_url, when, tiktok_desc=None):
    body = {"content": content, "platforms": accounts,
            "mediaItems": [{"url": media_url, "type": "image"}]}
    if tiktok_desc is not None:
        body["tiktokSettings"] = {"description": tiktok_desc,
                                  "privacy_level": "PUBLIC_TO_EVERYONE"}
    if when == "now":
        body["publishNow"] = True
    elif when:
        body["scheduledFor"] = when; body["timezone"] = TIMEZONE
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--schedule", default=None, help="ISO time to schedule instead of posting now")
    ap.add_argument("--key", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    key = a.key or (open(KEYFILE).read().strip() if os.path.exists(KEYFILE) else None)
    if not key and not a.dry_run:
        sys.exit("No API key. Put it in .zernio_key or pass --key sk_xxx")

    data = json.load(open(QUEUE))
    posts = data["posts"]
    pending = [p for p in posts if not p.get("used")]
    if not pending:
        print("Queue is empty - ask Claude to generate more posts.")
        return
    batch = pending[:a.count]
    when = "now" if not a.schedule else a.schedule
    print(f"Posting {len(batch)} item(s) {'NOW' if when=='now' else 'scheduled '+when}:\n")

    for p in batch:
        if not p.get("img_url") and not os.path.exists(os.path.join(MEDIA, p.get("img", ""))):
            print(f"  [skip] missing image for {p['id']}"); continue
        try:
            media_url = upload(p, key, a.dry_run)
        except Exception as e:
            print(f"  [FAIL upload] {p['id']}: {e}"); continue

        jobs = [("IG+FB", [FB, IG], p["ig_fb_caption"], None),
                ("TikTok", [TT], p["tiktok_title"], p.get("tiktok_description"))]
        ok_all = True
        for tag, accts, content, tt_desc in jobs:
            if a.dry_run:
                print(f"  [dry] {p['id']:<22} {tag}"); continue
            st, j = api("POST", "/posts", key, body=make_body(content, accts, media_url, when, tt_desc))
            ok = st in (200, 201)
            ok_all = ok_all and ok
            print(f"  [{'ok' if ok else 'FAIL'}] {p['id']:<22} {tag:<7} ({st})")
            if not ok:
                print(f"         -> {str(j)[:180]}")
            time.sleep(1)
        if ok_all and not a.dry_run:
            p["used"] = True

    if not a.dry_run:
        json.dump(data, open(QUEUE, "w"), indent=1, ensure_ascii=False)
    left = sum(1 for p in posts if not p.get("used"))
    print(f"\nDone. {left} posts left in the queue.")


if __name__ == "__main__":
    main()
