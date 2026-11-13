"""Instagram auto-poster (official Instagram API with Instagram Login).

Picks the first item in queue/ (alphabetical), publishes it, and moves it to posted/.

Queue item formats:
  queue/001_sunset.jpg  (+ optional queue/001_sunset.txt caption)   -> single photo
  queue/002_trip/        (2-10 .jpg files + optional caption.txt)   -> carousel
  queue/003_clip.mp4    (+ optional queue/003_clip.txt caption)    -> reel

Env:
  IG_ACCESS_TOKEN  long-lived Instagram user access token (required unless DRY_RUN=1)
  GITHUB_REPOSITORY, GITHUB_SHA  set automatically in GitHub Actions; used to build public raw URLs
  MEDIA_BASE_URL   optional override, e.g. https://example.com/media (path appended)
  DRY_RUN=1        print what would be posted without calling the API
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue"
POSTED = ROOT / "posted"
CONFIG = ROOT / "bot_config.json"
API = "https://graph.instagram.com/v23.0"

IMAGE_EXT = {".jpg", ".jpeg"}
VIDEO_EXT = {".mp4", ".mov"}


def load_config() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    return {}


def media_files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT | VIDEO_EXT)


def next_item() -> Path | None:
    for p in sorted(QUEUE.iterdir()):
        if p.name.startswith((".", "_")):
            continue
        if p.is_dir() and media_files(p):
            return p
        if p.is_file() and p.suffix.lower() in IMAGE_EXT | VIDEO_EXT:
            return p
    return None


def caption_for(item: Path, cfg: dict) -> str:
    txt = item / "caption.txt" if item.is_dir() else item.with_suffix(".txt")
    body = txt.read_text(encoding="utf-8").strip() if txt.exists() else cfg.get("default_caption", "")
    tags = cfg.get("hashtags", "").strip()
    return "\n\n".join(s for s in (body, tags) if s)[:2200]


def public_url(path: Path) -> str:
    rel = urllib.parse.quote(path.relative_to(ROOT).as_posix())
    base = os.environ.get("MEDIA_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{rel}"
    repo, sha = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_SHA")
    if not (repo and sha):
        sys.exit("GITHUB_REPOSITORY/GITHUB_SHA or MEDIA_BASE_URL must be set to build media URLs")
    return f"https://raw.githubusercontent.com/{repo}/{sha}/{rel}"


def api(method: str, path: str, token: str, **params) -> dict:
    params["access_token"] = token
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code} on {path}: {e.read().decode(errors='replace')}")


def wait_ready(cid: str, token: str, timeout: int = 600) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = api("GET", cid, token, fields="status_code,status").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {cid} failed: {status}")
        time.sleep(10)
    sys.exit(f"Container {cid} not ready after {timeout}s")


def create_container(user_id: str, token: str, f: Path, **extra) -> str:
    if f.suffix.lower() in VIDEO_EXT:
        params = {"media_type": "REELS", "video_url": public_url(f), **extra}
        if extra.get("is_carousel_item"):
            params["media_type"] = "VIDEO"
    else:
        params = {"image_url": public_url(f), **extra}
    cid = api("POST", f"{user_id}/media", token, **params)["id"]
    wait_ready(cid, token)
    return cid


def publish(item: Path, caption: str, token: str) -> str:
    me = api("GET", "me", token, fields="user_id,username")
    user_id = me.get("user_id") or me["id"]
    print(f"Posting as @{me.get('username')}")
    if item.is_dir():
        files = media_files(item)[:10]
        if len(files) < 2:
            sys.exit(f"Carousel {item.name} needs 2-10 media files")
        children = [create_container(user_id, token, f, is_carousel_item="true") for f in files]
        cid = api("POST", f"{user_id}/media", token, media_type="CAROUSEL",
                  children=",".join(children), caption=caption)["id"]
        wait_ready(cid, token)
    else:
        cid = create_container(user_id, token, item, caption=caption)
    return api("POST", f"{user_id}/media_publish", token, creation_id=cid)["id"]


def archive(item: Path) -> None:
    POSTED.mkdir(exist_ok=True)
    moves = [item] if item.is_dir() else [item, item.with_suffix(".txt")]
    for src in moves:
        if src.exists():
            dst = POSTED / src.name
            if subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT, capture_output=True).returncode:
                shutil.move(str(src), str(dst))


def main() -> None:
    item = next_item()
    if not item:
        print("Queue is empty; nothing to post.")
        return
    caption = caption_for(item, load_config())
    print(f"Next item: {item.relative_to(ROOT)}\nCaption:\n{caption}\n")

    if os.environ.get("DRY_RUN") == "1":
        files = media_files(item) if item.is_dir() else [item]
        for f in files:
            print("Media URL:", public_url(f))
        print("DRY_RUN=1 -> not posting.")
        return

    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        sys.exit("IG_ACCESS_TOKEN is not set")
    media_id = publish(item, caption, token)
    print(f"Published media id {media_id}")
    archive(item)


if __name__ == "__main__":
    main()
