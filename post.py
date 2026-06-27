#!/usr/bin/env python3
"""
Agosto Studio - unified social poster.

Posts / schedules the content in content-manifest.json to Facebook, Instagram,
and TikTok using the official platform APIs. No browser, no clicking.

Run modes
---------
  python3 post.py --test            Post ONLY post1 to every configured platform (pipeline check).
  python3 post.py --id post2-time   Post one specific item by id.
  python3 post.py --due             Post every item whose calendar date == today (used by the cron job).
  python3 post.py --all             Post every item in the manifest right now.
  add --dry-run to any command      Show exactly what WOULD be sent, call no APIs.

Credentials come from environment variables (a local .env file or GitHub Actions
secrets) - never hard-code them. See SETUP.md.

Required env vars
-----------------
  FB_PAGE_ID            Facebook Page numeric id
  FB_PAGE_TOKEN         Long-lived Page access token (also used for Instagram)
  IG_USER_ID            Instagram Business account id (connected to the Page)
  TIKTOK_ACCESS_TOKEN   TikTok access token with video.publish / photo scope
  MEDIA_BASE_URL        Public base URL where the post images are hosted
                        (e.g. https://raw.githubusercontent.com/<you>/<repo>/main/media)
Optional
  TIKTOK_PRIVACY        SELF_ONLY (default, required until your TikTok app is audited)
                        or PUBLIC_TO_EVERYONE once audited.
  PLATFORMS             Comma list to override per run, e.g. "instagram,facebook"
  LAUNCH_START_DATE     YYYY-MM-DD the 14-day calendar starts (default: today). Used by --due.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: pip install requests")

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "content-manifest.json"
GRAPH = "https://graph.facebook.com/v21.0"
TIKTOK = "https://open.tiktokapis.com/v2"


def env(name, default=None, required=False):
    val = os.environ.get(name, default)
    if required and not val:
        sys.exit(f"Missing required env var: {name}")
    return val


def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def media_url(base, filename):
    return f"{base.rstrip('/')}/{filename}"


def full_caption(post):
    tags = " ".join(post.get("hashtags", []))
    return (post["caption"] + ("\n\n" + tags if tags else "")).strip()


# --------------------------------------------------------------------------- #
#  Facebook (Page photo post)
# --------------------------------------------------------------------------- #
def post_facebook(post, img, caption, dry):
    if dry:
        return ("DRY", f"POST {GRAPH}/<FB_PAGE_ID>/photos url={img}")
    page_id = env("FB_PAGE_ID", required=True)
    token = env("FB_PAGE_TOKEN", required=True)
    url = f"{GRAPH}/{page_id}/photos"
    payload = {"url": img, "caption": caption, "access_token": token}
    r = requests.post(url, data=payload, timeout=60)
    ok = r.status_code == 200
    return ("OK" if ok else "FAIL", r.text)


# --------------------------------------------------------------------------- #
#  Instagram (2-step: create container, then publish)
# --------------------------------------------------------------------------- #
def post_instagram(post, img, caption, dry):
    if dry:
        return ("DRY", f"create+publish IG container url={img}")
    ig_id = env("IG_USER_ID", required=True)
    token = env("FB_PAGE_TOKEN", required=True)
    create = requests.post(
        f"{GRAPH}/{ig_id}/media",
        data={"image_url": img, "caption": caption, "access_token": token},
        timeout=60,
    )
    if create.status_code != 200:
        return ("FAIL", f"container: {create.text}")
    cid = create.json().get("id")
    # IG needs a moment to fetch/process the media before publish.
    time.sleep(5)
    pub = requests.post(
        f"{GRAPH}/{ig_id}/media_publish",
        data={"creation_id": cid, "access_token": token},
        timeout=60,
    )
    ok = pub.status_code == 200
    return ("OK" if ok else "FAIL", pub.text)


# --------------------------------------------------------------------------- #
#  TikTok (photo post via Content Posting API, PULL_FROM_URL)
# --------------------------------------------------------------------------- #
def post_tiktok(post, img, caption, dry):
    privacy = env("TIKTOK_PRIVACY", "SELF_ONLY")
    if dry:
        return ("DRY", f"POST {TIKTOK}/post/publish/content/init/ privacy={privacy} url={img}")
    token = env("TIKTOK_ACCESS_TOKEN", required=True)
    body = {
        "post_info": {
            "title": post["hook"],
            "description": caption,
            "privacy_level": privacy,
            "disable_comment": False,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_cover_index": 0,
            "photo_images": [img],
        },
        "post_mode": "DIRECT_POST",
        "media_type": "PHOTO",
    }
    r = requests.post(
        f"{TIKTOK}/post/publish/content/init/",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json; charset=UTF-8"},
        json=body,
        timeout=60,
    )
    ok = r.status_code == 200 and r.json().get("error", {}).get("code") in (None, "ok")
    return ("OK" if ok else "FAIL", r.text)


HANDLERS = {
    "facebook": post_facebook,
    "instagram": post_instagram,
    "tiktok": post_tiktok,
}


def run_post(post, manifest, platforms, dry):
    base = env("MEDIA_BASE_URL", required=not dry)
    img = media_url(base or "https://MEDIA_BASE_URL", post["image"])
    caption = full_caption(post)
    print(f"\n=== {post['id']}  ({post['hook']}) ===")
    results = {}
    for p in platforms:
        handler = HANDLERS.get(p)
        if not handler:
            results[p] = ("SKIP", "no handler")
            continue
        try:
            status, detail = handler(post, img, caption, dry)
        except Exception as e:  # noqa
            status, detail = "ERROR", str(e)
        results[p] = (status, detail)
        flag = {"OK": "[ok]", "DRY": "[dry]"}.get(status, "[!!]")
        print(f"  {flag} {p:<10} {status}  {detail[:200]}")
    return results


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true", help="post post1 only")
    g.add_argument("--id", help="post a single item by id")
    g.add_argument("--due", action="store_true", help="post items scheduled for today")
    g.add_argument("--all", action="store_true", help="post everything now")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_manifest()
    posts = manifest["posts"]
    override = env("PLATFORMS")
    platforms = [p.strip() for p in override.split(",")] if override \
        else manifest["default_platforms"]

    if args.test:
        selected = [posts[0]]
    elif args.id:
        selected = [p for p in posts if p["id"] == args.id]
        if not selected:
            sys.exit(f"No post with id '{args.id}'")
    elif args.all:
        selected = posts
    else:  # --due
        start = env("LAUNCH_START_DATE")
        start_date = dt.date.fromisoformat(start) if start else dt.date.today()
        today_offset = (dt.date.today() - start_date).days + 1  # day 1 == start date
        selected = [p for p in posts if p.get("calendar_day") == today_offset]
        if not selected:
            print(f"Nothing scheduled for launch day {today_offset} ({dt.date.today()}).")
            return

    print(f"Platforms: {platforms}   Dry-run: {args.dry_run}   Items: {[p['id'] for p in selected]}")
    any_fail = False
    for post in selected:
        res = run_post(post, manifest, platforms, args.dry_run)
        if any(s not in ("OK", "DRY") for s, _ in res.values()):
            any_fail = True
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
