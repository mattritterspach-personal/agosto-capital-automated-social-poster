#!/usr/bin/env python3
"""
Agosto Studio - Zernio launcher (full automation, no browser).

Reads the post images straight from disk at full quality, uploads them to Zernio,
then publishes the first three posts immediately to Instagram, Facebook, and TikTok
and schedules the rest across the launch calendar.

USAGE
-----
  1. Get a Zernio API key:  zernio.com  ->  Dashboard  ->  API Keys  ->  create key.
  2. Run:
        python3 zernio_launch.py YOUR_API_KEY
     Options:
        --now N        how many posts to publish immediately (default 3)
        --dry-run      show what would happen, call nothing
        --start-hour H hour (local) to schedule the remaining posts (default 10)

Only the standard library is used - no pip install needed.
"""

import sys, os, json, time, argparse, datetime as dt, mimetypes
import urllib.request, urllib.error

BASE = "https://zernio.com/api/v1"
TIMEZONE = "America/New_York"
MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")

# Connected Agosto Capital accounts (discovered from your Zernio account)
FB = {"platform": "facebook",  "accountId": "6a40373e9d9472faae08d5fd"}
IG = {"platform": "instagram", "accountId": "6a4036e09d9472faae08d2b8"}
TT = {"platform": "tiktok",    "accountId": "6a4036c39d9472faae08d1c4"}
# IG + FB take the full caption. TikTok photo posts use the caption AS the
# slideshow title (90-char cap), so TikTok gets its own short title instead.
FEED_ACCOUNTS = [FB, IG]
TIKTOK_ACCOUNTS = [TT]

# Short TikTok slideshow titles (<= 90 chars), keyed by image filename.
TT_TITLES = {
    "post1-launch.png":     "Agosto Studio is live. Five guides to help you buy back your life. Link in bio.",
    "post2-time.png":       "You don't have a time problem. You have an undefended calendar. Link in bio.",
    "post3-direction.png":  "You're not lazy. You just don't have a direction yet. Link in bio.",
    "post6-confidence.png": "Confidence isn't a feeling. It's evidence you collect. Link in bio.",
    "post5-status.png":     "Status isn't loud. The highest-status move in any room is restraint.",
    "post4-peace.png":      "Your kids aren't the problem. Your house just has no rhythm yet. Link in bio.",
    "post7-bundle.png":     "5 guides, 1 mission: buy back your life. The bundle is $59, over 50% off.",
}

POSTS = [
    {"img": "post1-launch.png", "title": "It's live.", "content":
"""It's live. Agosto Studio is here.

Five no-fluff guides to help you buy back your life: your time, your peace, your status, your confidence, and your direction.

No 300 pages of theory. Each one is a do-it-with-me system with worksheets and a plan you can actually run this week.

Start with the one you need most, or grab all five in the bundle and save over 50%.

Which one do you need first: time, peace, status, confidence, or direction? Tell me below.

Link in bio to shop them all.

#selfimprovement #personalgrowth #productivity #digitaldownloads #buybackyourtime"""},
    {"img": "post2-time.png", "title": "You don't have a time problem.", "content":
"""You don't have a time problem. You have an undefended calendar.

Every open hour gets claimed by whoever asks first: a meeting, a message, a "quick favor." None of it is evil. Together it's a slow leak that drains your whole week.

The fix isn't more willpower or a new app. It's a system that decides things in advance, so you stop re-deciding the same low-value tasks 40 times a day.

That system is the whole point of Buy Back Your Hours. Time audit, the Four D's, your Buy-Back Rate, and a 30-day plan to get 10+ hours a week back.

Save this so you remember it at 9pm when the inbox is still open.

#timemanagement #productivityhacks #worklifebalance #founders #getmoredone"""},
    {"img": "post3-direction.png", "title": "You're not lazy.", "content":
"""You're not lazy. You just don't have a direction yet.

You can't be motivated toward a blank. Most "I have no discipline" actually means "I have no decided next step." Get the direction first and the motivation follows it.

Start Here: Direction Map is a do-it-in-one-sitting workbook. Four questions to find your path, a 3-paths grid to choose it, and a 90-day plan to actually move on it. About 20 minutes to go from foggy to one clear sentence.

Everything's in our bio. Start with the one that's been on your mind.

#findyourpurpose #careerchange #motivationdaily #personaldevelopment #clarity"""},
    {"img": "post6-confidence.png", "title": "Confidence isn't a feeling.", "content":
"""Confidence isn't a feeling. It's evidence you collect.

You will not "feel ready" into confidence. You build it: small kept promises, reps that prove you can, and a way to shut up the inner critic that rewrites every win as luck.

The Confidence Reset is the system. Collect the evidence, run the 3-column trick on your self-talk, and walk in sure, on the days you feel it and the days you don't.

It starts in our bio. Build the evidence, one rep at a time.

#confidence #selfworth #womenempowerment #personalgrowth #mindsetshift"""},
    {"img": "post5-status.png", "title": "Status isn't loud.", "content":
"""Status isn't loud. The highest-status move in any room is restraint.

The guy trying hardest to look important almost never is. Real status is quiet: you don't over-explain, you don't chase the laugh, you don't need the room to react. Fit beats brand. Calm beats loud. Restraint beats flash.

The Status Playbook breaks down the silent signals, decoded and made practical, so respect comes to you instead of you reaching for it.

Follow for more. Link in bio for the full playbook.

#selfdevelopment #mensmindset #charisma #disciplineequalsfreedom #highvalueman"""},
    {"img": "post4-peace.png", "title": "Your kids aren't the problem.", "content":
"""Your kids aren't the problem. Your house just has no rhythm yet.

Meltdowns, mornings that feel like a fire drill, the constant low-grade noise. It's rarely the kids. It's that the day has no predictable shape, so every small thing becomes a negotiation.

Calm House, Clear Mind is the rhythm: simple routines, a 10-minute reset, and 3-sentence scripts that stop a meltdown without yelling. A calmer home and a clearer head, on purpose.

Save this for the 5pm meltdown. Link in bio when you're ready for the whole system.

#momlife #parentingtips #gentleparenting #calmhome #overwhelmedmom"""},
    {"img": "post7-bundle.png", "title": "5 guides. 1 mission.", "content":
"""5 guides. 1 mission: buy back your life.

Time. Peace. Status. Confidence. Direction. The whole Agosto Studio library in one bundle, for $59 instead of $120. That's over 50% off, and it's yours to keep.

If you've been picking which problem to fix first, this is the "fix all of it" option. Instant download, do-it-with-me worksheets, a plan for each.

Link in bio. Your future self is already annoyed you waited.

#digitalproducts #selfimprovement #personalgrowth #investinyourself #bundle"""},
]


def api(method, path, key, body=None, raw=None, ctype=None, full_url=None):
    url = full_url or (BASE + path)
    data = None
    headers = {}
    if key:
        headers["Authorization"] = "Bearer " + key
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = ctype or "application/octet-stream"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt and txt.strip().startswith(("{", "[")) else txt)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def upload(img_path, key, dry):
    fname = os.path.basename(img_path)
    ctype = mimetypes.guess_type(fname)[0] or "image/png"
    if dry:
        return "https://DRY/" + fname
    st, j = api("POST", "/media", key, body={"filename": fname, "contentType": ctype})
    if st != 200 or not isinstance(j, dict):
        raise RuntimeError(f"presign failed ({st}): {j}")
    with open(img_path, "rb") as f:
        raw = f.read()
    pst, _ = api("PUT", None, None, raw=raw, ctype=ctype, full_url=j["uploadUrl"])
    if pst not in (200, 201, 204):
        raise RuntimeError(f"PUT failed ({pst})")
    return j["publicUrl"]


def create_post(content, accounts, media_url, key, when, dry):
    body = {
        "content": content,
        "platforms": accounts,
        "mediaItems": [{"url": media_url, "type": "image"}],
    }
    if when == "now":
        body["publishNow"] = True
    elif when:
        body["scheduledFor"] = when
        body["timezone"] = TIMEZONE
    if dry:
        return 200, {"dry": True, "when": when}
    return api("POST", "/posts", key, body=body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("api_key")
    ap.add_argument("--now", type=int, default=3, help="publish first N immediately")
    ap.add_argument("--start-hour", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    today = dt.date.today()
    print(f"Agosto Studio launch -> publishing {a.now} now, scheduling {len(POSTS)-a.now} more.\n")
    sched_day = 1
    for i, p in enumerate(POSTS):
        img = os.path.join(MEDIA_DIR, p["img"])
        if not os.path.exists(img):
            print(f"  [skip] missing {p['img']}"); continue
        try:
            media_url = upload(img, a.api_key, a.dry_run)
        except Exception as e:
            print(f"  [FAIL upload] {p['img']}: {e}"); continue

        if i < a.now:
            when = "now"; label = "PUBLISH NOW"
        else:
            d = today + dt.timedelta(days=sched_day)
            when = f"{d.isoformat()}T{a.start_hour:02d}:00:00"
            label = f"schedule {d.isoformat()} {a.start_hour:02d}:00"
            sched_day += 1

        tt_title = TT_TITLES.get(p["img"], p["title"])[:90]
        jobs = [("IG+FB", FEED_ACCOUNTS, p["content"]),
                ("TikTok", TIKTOK_ACCOUNTS, tt_title)]
        for tag, accounts, content in jobs:
            st, j = create_post(content, accounts, media_url, a.api_key, when, a.dry_run)
            ok = st in (200, 201)
            print(f"  [{'ok' if ok else 'FAIL'}] {p['img']:<22} {tag:<7} {label}  ({st})")
            if not ok:
                print(f"         -> {str(j)[:200]}")
            time.sleep(1)
    print("\nDone. Check zernio.com -> Posts, and your IG / FB / TikTok.")


if __name__ == "__main__":
    main()
