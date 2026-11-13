---
name: ig-queue
description: >-
  Put approved Instagram content into this repo's auto-post queue so the
  GitHub Actions bot publishes it. Use when the user says "queue this",
  "schedule this", "post this", "add it to the queue", "put it in the queue",
  or approves a caption/carousel/reel made with the other /ig-* skills and
  wants it posted automatically.
---

# ig-queue

This repo has a bot (`bot/post.py`, `.github/workflows/post.yml`) that posts
**one item from `queue/` per scheduled run**, in filename order, then moves it
to `posted/`. This skill turns approved content into items in that queue.
It never posts directly. The workflow does, once the changes reach `main`.

## Only after approval

Queue only content the user has explicitly approved. Run captions through
`/ig-human` first if they have not been yet.

## Naming

Look at the existing names in `queue/` and pick the next number
(`001_`, `002_` ...). Add a short ASCII slug: `004_contract-clause`.
If the user gave dates from `/ig-plan`, order the numbers in the plan's order.
The bot posts one per run (daily by default), so the position in the queue is
the posting day.

## Formats the bot accepts

| Content | Files |
|---|---|
| Single photo | `queue/NNN_slug.jpg` + `queue/NNN_slug.txt` (caption) |
| Carousel | `queue/NNN_slug/01.jpg ... 10.jpg` + `queue/NNN_slug/caption.txt` |
| Reel | `queue/NNN_slug.mp4` + `queue/NNN_slug.txt` |

Hard limits, check them before you write files:
- Images must be **JPEG**. Convert PNG/WebP first.
- Aspect ratio between **4:5 and 1.91:1**. 1080x1350 is the safe default.
- Carousels hold **2 to 10** items (the API caps at 10, even though the app allows 20).
- Caption at most 2,200 characters, at most 30 hashtags. The bot also appends
  `hashtags` from `bot_config.json`, so do not duplicate those.

## Rendering carousel slides to JPEG

When `/ig-carousel` produced HTML slides, render each one to its own JPEG:

```js
// render.js <slides.html> <out_dir>   (one <section class="slide"> per slide)
// Needs Node + Playwright (`npm i playwright && npx playwright install chromium`
// on a fresh machine; Claude Code cloud sessions already have it).
const { chromium } = require('playwright');
const path = require('path');
const [html, out] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  await page.goto('file://' + path.resolve(html));
  const slides = await page.$$('section.slide');
  for (let i = 0; i < slides.length; i++) {
    const name = String(i + 1).padStart(2, '0') + '.jpg';
    await slides[i].screenshot({ path: path.join(out, name), type: 'jpeg', quality: 92 });
  }
  await browser.close();
})();
```

Each slide's HTML must be exactly `width:1080px; height:1350px`, and the page
needs `body { margin: 0 }`.

Keep the HTML and the script outside `queue/` (e.g. in `instagram/drafts/`).
The bot treats every `.jpg` in a carousel folder as a slide.

## Finish

1. Run the dry run to confirm what posts next:
   `GITHUB_REPOSITORY=<owner>/<repo> GITHUB_SHA=main DRY_RUN=1 python3 bot/post.py`
2. Show the user the queue in order, with the day each item will go out.
3. Append to `instagram/log.md`: the date queued, the file name, the format,
   and the hook or first line. `/ig-audit` reads this later.
4. Commit. Remind the user that the workflow only sees what is on `main`.
