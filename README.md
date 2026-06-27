# Agosto Studio Social Poster

Automated social posting for Agosto Studio (Instagram, Facebook, TikTok) via the
[Zernio](https://zernio.com) API. Write once, post on demand or on a schedule, and
keep a self-refilling queue of on-brand content.

## What it does

- **Posts to IG, Facebook, and TikTok** from a single content queue.
- Each queue item becomes an **IG + Facebook post** (full caption) plus a separate
  **TikTok post** with a short title and a distinct caption (TikTok photo posts use
  the caption as the slideshow title, capped at 90 characters, so they're kept
  separate to avoid repetition).
- Content is a **mix of branded gradient quote-cards and real stock photos**.

## Files

| File | Purpose |
|------|---------|
| `agosto_run.py` | Posts the next N unused queue items (default 2) to all platforms. Supports local images (`img`) and remote stock photos (`img_url`, downloaded at run time). |
| `content_queue.json` | The content queue. Each post: `id`, caption fields, `used` flag, and either `img` or `img_url`. |
| `generate_content.py` | Renders new on-brand gradient quote-card images (weasyprint + pymupdf) and appends them to the queue. |
| `zernio_launch.py` | One-time launch script: posts 3 immediately and schedules the rest. |
| `Post 2 to Social.command` | Double-click to post the next 2 items now. |
| `run.command` | Same as above (CLI passthrough to `agosto_run.py`). |
| `Install Auto-Posting.command` | Installs a launchd agent that auto-posts 2/platform daily at 10am. |
| `Stop Auto-Posting.command` | Removes the launchd agent. |
| `com.agosto.socialposter.plist` | The launchd agent definition. |
| `media/` | Generated quote-card images. |

## Setup

1. Connect Instagram, Facebook, and TikTok accounts in your Zernio dashboard.
2. Create a Zernio API key (Dashboard → API Keys) and save it to a file named
   `.zernio_key` in this folder (one line, just the key). **This file is gitignored
   and must never be committed.**
3. Post on demand: `python3 agosto_run.py` (or double-click `Post 2 to Social.command`).
4. Auto-post daily: double-click `Install Auto-Posting.command` once.

## Usage

```bash
python3 agosto_run.py                 # post next 2 items now
python3 agosto_run.py --count 3       # post next 3
python3 agosto_run.py --schedule "2026-07-10T10:00"   # schedule instead of now
python3 agosto_run.py --dry-run       # preview, send nothing
```

## Queue refill

The queue is kept stocked by a scheduled task that, when fewer than 6 unused posts
remain, writes a fresh batch of captions paired with stock photos. New branded
quote-cards can be generated any time with `generate_content.py`.

## Notes

- Only the Python standard library is required to post (`agosto_run.py`).
  `generate_content.py` needs `weasyprint` and `pymupdf`.
- Stock photos are sourced from Unsplash (free for commercial use).
- No secrets are stored in this repo; the API key lives only in the local,
  gitignored `.zernio_key` file.
