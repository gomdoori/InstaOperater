# InstaOperater — Instagram auto-post bot

Put photos or videos in the `queue/` folder and GitHub Actions posts **one a day** to Instagram on its own.
It uses Meta's **official Instagram API**, so there's very little risk of the account being suspended. No server needed, and it's free.

## Making content with Claude: `/ig-*` commands

When you open this repo in Claude Code, these commands work right away (from [instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill), MIT).

| Command | What it does |
|---|---|
| `/ig-plan` | Plans the week: what to post, in what format, when |
| `/ig-caption` | Writes the caption + hashtags |
| `/ig-carousel` | Writes carousel slide copy + makes images |
| `/ig-reel` | Writes the reel script and scores the hook |
| `/ig-profile` | Scores the profile out of 100 + suggests fixes |
| `/ig-human` | Removes phrasing that sounds like AI wrote it |
| `/ig-queue` | **Puts approved content into `queue/`** → the bot posts it automatically |
| Others | `/ig-viral` `/ig-story` `/ig-comment` `/ig-reply` `/ig-dm` `/ig-repurpose` `/ig-audit` |

Typical flow: `/ig-plan` → `/ig-carousel` or `/ig-caption` → approve → `/ig-queue` → merge into main → one post a day goes up automatically

Fill in `instagram/voice.md` (your account's tone of voice) first, and every skill will write in that voice. Plans, logs and the rest are also saved in the `instagram/` folder.

## How it works

```
queue/  ──(daily at 08:47 KST, GitHub Actions)──▶ post to Instagram ──▶ move to posted/
```

- Items post in filename order (put numbers in front of names: `001_`, `002_` …)
- The media files are served to Instagram through the public raw URL of this repository (so the **repository must stay public**)

## Queue format

| What to post | How to put it in |
|---|---|
| Single photo | `queue/001_sunset.jpg` + (optional) `queue/001_sunset.txt` ← caption |
| Carousel (2–10 photos) | `queue/002_trip/` folder holding `1.jpg`, `2.jpg` … + (optional) `caption.txt` |
| Reel | `queue/003_clip.mp4` + (optional) `queue/003_clip.txt` |

- Photos must be **JPEG** only (convert PNG to JPG). Aspect ratio between 4:5 and 1.91:1
- If there's no caption file, `default_caption` in `bot_config.json` is used, and `hashtags` is always added at the end.
- Files or folders whose names start with `_` or `.` are skipped.

## One-time setup (about 10 minutes)

### 1. Switch the Instagram account to professional
Instagram app → Settings → Account type and tools → **Switch to professional account** (Creator or Business). You don't need to link a Facebook page.

### 2. Get an access token
1. Create an app at <https://developers.facebook.com/apps> (type: **Business**)
2. Add the **Instagram** product → choose **API setup with Instagram login**
3. Under *Generate access tokens*, add your Instagram account and click **Generate token**
   - Permissions: `instagram_business_basic`, `instagram_business_content_publish`
4. Copy the token that's shown (a long-lived token, valid for 60 days)

> The app can stay in development mode. Since you're only posting to your own account, you don't need app review.

### 3. Register the GitHub Secret
Repository → **Settings → Secrets and variables → Actions → New repository secret**
- `IG_ACCESS_TOKEN` = the token from step 2

### 4. (Recommended) Automatic token renewal
The token expires after 60 days. If you also register `GH_PAT`, the `refresh-token.yml` workflow renews it every week.
- <https://github.com/settings/personal-access-tokens> → Fine-grained token → only this repository → **Secrets: Read and write**
- Register it as a Secret named `GH_PAT`

### 5. Test
Actions tab → **Instagram auto post** → *Run workflow*
- `dry_run` = `1`: only checks which item would be posted
- `dry_run` = `0`: actually posts right away

## Settings

- **Posting time / frequency**: change `cron` in `.github/workflows/post.yml` (UTC). For example, twice a day: `"47 23 * * *"` and `"17 9 * * *"` on two lines
- **Default caption / hashtags**: `bot_config.json`

> ⚠️ GitHub only runs scheduled workflows from the **default branch (main)**. Merge this branch into main first.

## Local test

```bash
GITHUB_REPOSITORY=gomdoori/InstaOperater GITHUB_SHA=main DRY_RUN=1 python3 bot/post.py
```
