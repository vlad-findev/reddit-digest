"""Personal read-only Reddit digest.

Usage:
    python digest.py            # live run (requires approved API access)
    python digest.py --sample   # run on sample_data/posts.json
"""

import argparse
import json
import logging
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("reddit-digest")


def load_config():
    with open(BASE / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_live(cfg):
    """Fetch posts from Reddit via PRAW. Read-only: no write calls are made."""
    import praw
    from dotenv import load_dotenv

    load_dotenv(BASE / ".env")
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=f"reddit-digest/0.1 by u/{os.environ['REDDIT_USERNAME']}",
    )
    reddit.read_only = True

    posts = []
    for name in cfg["subreddits"]:
        try:
            posts.extend(fetch_subreddit(reddit.subreddit(name), name, cfg))
        except Exception as e:  # private, banned or renamed subreddit, network error
            log.warning("Skipping r/%s: %s", name, e)
        # Small pause between subreddits to keep the request rate low.
        time.sleep(cfg.get("request_delay", 1))
    return posts


def fetch_subreddit(sub, name, cfg):
    if cfg["sort"] == "top":
        items = sub.top(time_filter=cfg.get("time_filter", "day"), limit=cfg["limit"])
    elif cfg["sort"] == "hot":
        items = sub.hot(limit=cfg["limit"])
    else:
        items = sub.new(limit=cfg["limit"])
    result = []
    for p in items:
        if p.stickied:  # skip pinned mod posts, they repeat every day
            continue
        # Only post-level fields; author names are intentionally not stored.
        result.append({
            "subreddit": name,
            "title": p.title,
            "selftext": p.selftext[:500],
            "score": p.score,
            "num_comments": p.num_comments,
            "created_utc": p.created_utc,
            "permalink": f"https://www.reddit.com{p.permalink}",
        })
    return result


def fetch_sample():
    with open(BASE / "sample_data" / "posts.json", encoding="utf-8") as f:
        return json.load(f)


def build_digest(posts, cfg):
    today = date.today().isoformat()
    lines = [f"# Reddit digest, {today}", ""]
    for name in cfg["subreddits"]:
        sub_posts = sorted(
            (p for p in posts if p["subreddit"].lower() == name.lower()),
            key=lambda p: p["score"],
            reverse=True,
        )
        if not sub_posts:
            continue
        lines += [f"## r/{name}", ""]
        for p in sub_posts:
            ts = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc).strftime("%H:%M UTC")
            lines.append(
                f"- [{p['title']}]({p['permalink']}) ({p['score']} points, {p['num_comments']} comments, {ts})"
            )
            if p.get("selftext"):
                snippet = p["selftext"].replace("\n", " ").strip()
                lines.append(f"  > {snippet[:200]}{'...' if len(snippet) > 200 else ''}")
        lines.append("")
    return "\n".join(lines)


def cleanup(retention_days):
    cutoff = time.time() - retention_days * 86400
    for f in OUTPUT_DIR.glob("digest-*.md"):
        if f.stat().st_mtime < cutoff:
            f.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="use sample data instead of the API")
    args = parser.parse_args()

    cfg = load_config()
    posts = fetch_sample() if args.sample else fetch_live(cfg)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"digest-{date.today().isoformat()}.md"
    out.write_text(build_digest(posts, cfg), encoding="utf-8")
    cleanup(cfg.get("retention_days", 7))
    log.info("Digest written to %s (%d posts)", out, len(posts))


if __name__ == "__main__":
    main()
