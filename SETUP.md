# Agosto Studio - Automated Posting Setup

This pipeline posts and schedules to **Facebook, Instagram, and TikTok** using the
official platform APIs. No browser automation, no clicking, no per-post approvals.
You do the credential setup **once** (~30-45 min), then it runs itself for free.

## How it works

```
content-manifest.json + /media images
        │
   post.py  (calls Meta Graph API + TikTok Content Posting API directly)
        │
GitHub Actions cron  →  runs post.py --due every day  →  posts what's scheduled
```

Two ways to run it:
- **GitHub Actions (recommended)** - free, runs in the cloud on a schedule, your Mac
  can be off. This is what makes it truly hands-free.
- **Local on your Mac** - run `./run_local.sh` manually or via `cron`/`launchd`
  (only fires when the Mac is awake).

---

## One-time setup

### Step 1 - Host the media (gives Instagram a public image URL)

Instagram's API requires each image to be at a public URL. Easiest free option:
1. Create a **public** GitHub repo (e.g. `agosto-social`).
2. Push this whole `social-poster` folder into it.
3. Your image base URL becomes:
   `https://raw.githubusercontent.com/<your-username>/<repo>/main/digital-products/social-poster/media`
   That's your `MEDIA_BASE_URL`.

### Step 2 - Meta (Facebook + Instagram), ~20 min

You need: a Facebook **Page**, an Instagram **Business or Creator** account, and the
IG account linked to the Page (Page → Settings → Linked accounts).

1. Go to **developers.facebook.com** → create an app (type: **Business**).
2. Add the **Instagram Graph API** and **Facebook Login** products.
3. In **Graph API Explorer**, generate a **User token** with these permissions:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_content_publish`, `business_management`.
4. Exchange it for a **long-lived Page token** (the Access Token Debugger and the
   `/oauth/access_token?grant_type=fb_exchange_token` endpoint do this). Long-lived
   Page tokens last ~60 days; see Step 5 for keeping it fresh.
5. Collect these three values:
   - `FB_PAGE_ID` - GET `/me/accounts` returns your Page id.
   - `FB_PAGE_TOKEN` - the long-lived Page token from step 4.
   - `IG_USER_ID` - GET `/{FB_PAGE_ID}?fields=instagram_business_account`.

> While your Meta app is in **Development** mode you can publish to any IG/Page you
> have an admin role on. To post on behalf of other accounts later you'd submit for
> App Review - not needed for posting to your own Agosto Studio accounts.

### Step 3 - TikTok, ~15 min

1. Go to **developers.tiktok.com** → create an app.
2. Add the **Content Posting API** product and request the
   `video.publish` / `photo` scopes.
3. Authorize your Agosto TikTok account and generate an **access token** →
   `TIKTOK_ACCESS_TOKEN`.

> **Important TikTok limit:** until your app passes TikTok's **audit**, posts can
> only be created as **private (`SELF_ONLY`)** - they land in your account ready for
> you to tap publish, but can't auto-go-public. Keep `TIKTOK_PRIVACY=SELF_ONLY`
> until audited, then switch to `PUBLIC_TO_EVERYONE`. Apply for the audit in the
> TikTok developer portal once you've confirmed the pipeline works.

### Step 4 - Add the secrets

**GitHub Actions:** repo → Settings → Secrets and variables → Actions → New
repository secret. Add each of: `FB_PAGE_ID`, `FB_PAGE_TOKEN`, `IG_USER_ID`,
`TIKTOK_ACCESS_TOKEN`, `TIKTOK_PRIVACY`, `MEDIA_BASE_URL`, and (optional)
`LAUNCH_START_DATE` (YYYY-MM-DD the calendar begins).

**Local:** `cp .env.example .env` and fill in the same values.

### Step 5 - Test, then go live

1. **Dry run** (no posting): Actions tab → "Agosto Studio - scheduled social posts"
   → Run workflow → `--test --dry-run`. Confirms wiring with zero risk.
   Locally: `./run_local.sh --test --dry-run`.
2. **Real test post:** run again with `--test`. This posts **post1** to all three
   platforms. Check each account.
3. **Turn on the schedule:** the daily cron (`0 14 * * *` UTC) is already in
   `.github/workflows/scheduled-post.yml`. Edit the time if you like. It runs
   `post.py --due`, which posts whatever the manifest schedules for that day
   (via each post's `calendar_day` + your `LAUNCH_START_DATE`).

### Keeping tokens fresh

- **Meta** long-lived Page tokens last ~60 days. For permanent automation, create a
  **System User** in Meta Business Settings and issue a non-expiring System User
  token - recommended once you've validated the flow.
- **TikTok** tokens refresh via the refresh_token flow; add a refresh step when you
  move past testing.

---

## Editing what gets posted

Everything lives in `content-manifest.json`: caption, hook, hashtags, image file,
and `calendar_day`. Add/reorder posts there - no code changes needed. Drop new
images in `/media` and reference them by filename.
