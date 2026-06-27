#!/usr/bin/env python3
"""
Generate fresh on-brand Agosto Studio post images + a content_queue.json.
Reuses the gradient quote-card style of the original posts.

Run (in an env with weasyprint + pymupdf):
    python3 generate_content.py
It writes new PNGs into ./media and (re)writes ./content_queue.json with all
unused posts. Existing 'used' flags in a prior queue are preserved by id.
"""
import os, json, shutil
from weasyprint import HTML
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, "media")
QUEUE = os.path.join(HERE, "content_queue.json")
os.makedirs(MEDIA, exist_ok=True)

BASE = """
<style>
@page {{ size: 1080px 1080px; margin:0; }}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1080px;height:1080px;font-family:Poppins,'Lato',sans-serif;}}
.card{{width:1080px;height:1080px;position:relative;overflow:hidden;{bg};display:flex;flex-direction:column;padding:84px 80px;}}
.eyebrow{{font-weight:800;letter-spacing:.22em;text-transform:uppercase;font-size:26px;{eyecol};}}
.spacer{{flex:1;}}
.headline{{font-weight:800;line-height:1.03;letter-spacing:-.02em;{headcol};}}
.sub{{font-weight:500;line-height:1.4;{subcol};margin-top:32px;}}
.foot{{font-weight:700;font-size:26px;{footcol};}}
.blob{{position:absolute;border-radius:50%;filter:blur(8px);}}
</style>
<div class="card">{body}</div>
"""

# Per-theme palettes (match the original launch set)
THEMES = {
    "time":       dict(bg="background:linear-gradient(150deg,#1E3A8A 0%,#0EA5E9 100%);",
                       accent="#FFE66D", foot="No. 01 · Buy back your hours"),
    "peace":      dict(bg="background:linear-gradient(150deg,#FF7B54 0%,#FF2E7E 100%);",
                       accent="#FFE66D", foot="No. 02 · Find your peace"),
    "status":     dict(bg="background:linear-gradient(150deg,#0BA360 0%,#3CBA92 50%,#A8FF53 100%);",
                       accent="#063b27", foot="No. 03 · Sell your status"),
    "confidence": dict(bg="background:linear-gradient(145deg,#FF4D8D 0%,#A93AFF 60%,#6A2CFF 100%);",
                       accent="#FFE94A", foot="No. 04 · Build your confidence"),
    "direction":  dict(bg="background:linear-gradient(150deg,#0F766E 0%,#22C55E 100%);",
                       accent="#FDE047", foot="No. 05 · Find your direction"),
}


def render(name, theme, eyebrow, head1, head2, sub):
    t = THEMES[theme]
    body = f'''<div class="blob" style="width:500px;height:500px;background:{t['accent']};top:-140px;right:-120px;opacity:.35;"></div>
 <div class="eyebrow">{eyebrow}</div><div class="spacer"></div>
 <div class="headline" style="font-size:104px;color:#fff;">{head1}</div>
 <div class="headline" style="font-size:74px;margin-top:14px;color:{t['accent']};">{head2}</div>
 <div class="sub" style="font-size:36px;max-width:860px;color:rgba(255,255,255,.95);">{sub}</div>
 <div class="spacer"></div><div class="foot" style="color:#fff;">{t['foot']}</div>'''
    html = BASE.format(bg=t["bg"], eyecol="color:rgba(255,255,255,.9);", headcol="", subcol="", footcol="", body=body)
    pdf = os.path.join("/tmp", name + ".pdf")
    tmp_png = os.path.join("/tmp", name + ".png")
    target = os.path.join(MEDIA, name + ".png")
    HTML(string=html).write_pdf(pdf)
    d = fitz.open(pdf); d[0].get_pixmap(dpi=96).save(tmp_png); d.close()
    if not os.path.exists(target):           # mount blocks overwrite; only create new
        shutil.copyfile(tmp_png, target)
        print("image:", name)
    else:
        print("image (kept existing):", name)
    for f in (pdf, tmp_png):
        try: os.remove(f)
        except OSError: pass


# (img_name, theme, eyebrow, head1, head2, sub, ig_fb_caption, tiktok_title)
ITEMS = [
 ("gen-time-rate","time","No. 01 · Buy back your hours","I gave myself","a $75/hr rule.",
  "Anything below it, I stop doing. <b>Buy Back Your Hours</b>.",
  "I gave myself a $75/hr rule and it freed up 10 hours a week.\n\nHere's the move: put a dollar value on your hour, then ruthlessly delete, delegate, or automate everything that costs less than that to do yourself. You stop spending $75 hours on $10 tasks.\n\nThe full system, your Buy-Back Rate, the Four D's, and a 30-day plan, is in Buy Back Your Hours. Link in bio.\n\n#timemanagement #productivity #founders #worklifebalance #buybackyourtime",
  "I gave myself a $75/hr rule. It freed up 10 hours a week. Link in bio."),

 ("gen-time-4ds","time","No. 01 · Buy back your hours","The 4 D's","that deleted half my list.",
  "Do, Delegate, Defer, Delete. <b>Buy Back Your Hours</b>.",
  "The 4 D's that deleted half my to-do list.\n\nEvery task gets one: Do it now (under 2 min), Delegate it, Defer it to a real slot, or Delete it. Most lists are 40% Delete in disguise.\n\nRun your whole list through it once and watch it shrink. The full method is in Buy Back Your Hours, link in bio.\n\n#productivityhacks #timemanagement #getmoredone #founders #focus",
  "The 4 D's that deleted half my to-do list. Link in bio."),

 ("gen-peace-reset","peace","No. 02 · Find your peace","The 10-minute reset","that ended our chaos.",
  "One small routine, a calmer house. <b>Calm House, Clear Mind</b>.",
  "The 10-minute reset that ended our morning chaos.\n\nSame three steps, same time, every day: lay out tomorrow tonight, one shared checklist, and a 2-minute tidy before bed. The morning stops being a negotiation because the decisions are already made.\n\nThe full rhythm is in Calm House, Clear Mind. Save this for tomorrow morning. Link in bio.\n\n#momlife #parentingtips #calmhome #gentleparenting #routines",
  "The 10-minute reset that ended our morning chaos. Link in bio."),

 ("gen-peace-scripts","peace","No. 02 · Find your peace","3 sentences","that stop a meltdown.",
  "No yelling required. <b>Calm House, Clear Mind</b>.",
  "3 sentences that stop a meltdown without yelling.\n\n\"I can see you're upset.\" \"You can be upset and we still keep our hands safe.\" \"I'm right here when you're ready.\" Name it, hold the boundary, offer connection. It works because it lowers the temperature instead of raising it.\n\nMore scripts like this in Calm House, Clear Mind. Link in bio.\n\n#gentleparenting #parentingtips #momlife #calmhome #toddlers",
  "3 sentences that stop a meltdown without yelling. Link in bio."),

 ("gen-status-withhold","status","No. 03 · Sell your status","Stop performing","for attention.",
  "Withhold it. <b>The Status Playbook</b>.",
  "Stop performing for attention. Withhold it.\n\nThe person working hardest for the room's reaction is telling everyone they don't have it. Status is what you don't need: you don't over-explain, you don't chase the laugh, you don't fill every silence.\n\nThe silent signals, decoded, are in The Status Playbook. Follow for more. Link in bio.\n\n#mensmindset #charisma #selfdevelopment #highvalueman #discipline",
  "Stop performing for attention. Withhold it. Link in bio."),

 ("gen-status-room","status","No. 03 · Sell your status","High-status men","do this silently.",
  "And it changes every room. <b>The Status Playbook</b>.",
  "High-status men do one thing in every room, and it's silent.\n\nThey slow down. Slower speech, slower movements, longer pauses before answering. Speed reads as anxiety; stillness reads as control. You can't fake it with words, only with pace.\n\nThe full set of signals is in The Status Playbook. Link in bio.\n\n#charisma #mensmindset #selfimprovement #highvalueman #presence",
  "High-status men do this in every room, and it's silent. Link in bio."),

 ("gen-confidence-3col","confidence","No. 04 · Build your confidence","The 3-column trick","that quiets your critic.",
  "Thought, evidence, reframe. <b>The Confidence Reset</b>.",
  "The 3-column trick that shuts up your inner critic.\n\nColumn 1: the harsh thought. Column 2: the actual evidence for and against it. Column 3: the fairer, truer version. Your critic survives on being unexamined. Put it on paper and it shrinks.\n\nThe full system is in The Confidence Reset. Save this. Link in bio.\n\n#confidence #mindsetshift #selfworth #womenempowerment #personalgrowth",
  "The 3-column trick that shuts up your inner critic. Link in bio."),

 ("gen-confidence-10","confidence","No. 04 · Build your confidence","10 sentences","confident women keep ready.",
  "Borrow them until they're yours. <b>The Confidence Reset</b>.",
  "10 sentences every confident woman has ready.\n\n\"Let me think about that and get back to you.\" \"That doesn't work for me.\" \"I'd like to finish my point.\" Confidence is often just having the words before you need them, so you don't freeze and agree to things you don't want.\n\nThe full list and the system behind it are in The Confidence Reset. Link in bio.\n\n#womenempowerment #confidence #boundaries #selfworth #mindset",
  "10 sentences every confident woman has ready. Link in bio."),

 ("gen-direction-clarity","direction","No. 05 · Find your direction","Clarity beats","motivation.",
  "Get it in 20 minutes. <b>Start Here: Direction Map</b>.",
  "Clarity beats motivation. Here's how to get it in 20 minutes.\n\nMotivation chases a clear target; it can't chase a blank. Answer four questions on paper, what energizes you, what you're good at, what people pay for, what you'd do anyway, and the overlap is your direction.\n\nThe full workbook is Start Here: Direction Map. Link in bio.\n\n#findyourpurpose #clarity #motivation #personaldevelopment #careerchange",
  "Clarity beats motivation. Get it in 20 minutes. Link in bio."),

 ("gen-direction-4q","direction","No. 05 · Find your direction","The 4 questions","that found my next move.",
  "20 minutes, one clear sentence. <b>Start Here: Direction Map</b>.",
  "The 4 questions that found my next move.\n\nWhat would I do if no one was watching? What problem do I keep being drawn back to? What did I love before I was told it wasn't practical? What would the bravest version of me choose? Write fast, don't edit.\n\nThe full map from foggy to one clear sentence is Start Here: Direction Map. Link in bio.\n\n#direction #careerchange #findyourpurpose #clarity #personalgrowth",
  "The 4 questions that found my next move. Link in bio."),
]


def build():
    # render new images
    for name, theme, eyebrow, h1, h2, sub, *_ in ITEMS:
        render(name, theme, eyebrow, h1, h2, sub)

    # preserve used-flags from any existing queue
    used = {}
    if os.path.exists(QUEUE):
        try:
            for it in json.load(open(QUEUE)).get("posts", []):
                used[it["id"]] = it.get("used", False)
        except Exception:
            pass

    posts = []
    for name, theme, eyebrow, h1, h2, sub, ig_fb, tt_title in ITEMS:
        # TikTok shows tt_title as the slideshow title; drop the hook paragraph
        # from the caption so the title and caption don't repeat each other.
        parts = ig_fb.split("\n\n")
        tt_desc = "\n\n".join(parts[1:]) if len(parts) > 1 else ig_fb
        posts.append({
            "id": name,
            "img": name + ".png",
            "ig_fb_caption": ig_fb,
            "tiktok_title": tt_title[:90],
            "tiktok_description": tt_desc,
            "used": used.get(name, False),
        })
    json.dump({"posts": posts}, open(QUEUE, "w"), indent=1, ensure_ascii=False)
    print(f"\nqueue: {len(posts)} posts -> {QUEUE}")


if __name__ == "__main__":
    build()
