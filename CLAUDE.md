# InstaOperater

An Instagram account run from this repo.

- **Content**: `/ig-*` skills in `.claude/skills/` (from
  [instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill), MIT).
  They write content. They do not post.
- **Posting**: `bot/post.py` + `.github/workflows/post.yml` posts one item a day from `queue/`
  through the official Instagram API, then moves it to `posted/`.
- **Glue**: `/ig-queue` puts approved content into `queue/` in the format the bot accepts.

Shared data for the skills lives in `instagram/` (committed, so it survives sessions):
`voice.md` (account voice, every skill reads it), `plan.md`, `swipe.md`, `log.md`.
Drafts that should not be posted go in `instagram/drafts/`, never in `queue/`.

The user writes in Korean; answer in Korean and write captions in the language the
user asks for (default Korean).
