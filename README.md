# reddit-digest

A small personal, read-only automation that builds a daily digest of new and top posts from a handful of subreddits I follow (AI and financial market trends), so I can quickly see what is worth reading and then join the discussions on Reddit directly.

## What it does

- Authenticates with the Reddit Data API via OAuth (script app, read-only usage).
- Once or a few times a day, fetches new/top posts from the subreddits listed in `config.yaml`.
- Builds a short Markdown digest (title, score, comment count, link to the original thread).
- Optionally, a short summary of each post can be generated for personal reading (planned).

## What it does NOT do

- It never posts, comments, votes, or sends messages.
- It does not store or analyze user profiles and does not infer anything about individual users. Author names are not saved.
- Data is kept locally only as long as needed to build the digest (see `retention_days` in `config.yaml`).
- Data is not shared, sold, or used to train AI or ML models.

## API usage

- Library: [PRAW](https://praw.readthedocs.io/)
- Volume: roughly 20 to 40 requests per run (17 subreddits), 1 to 3 runs per day, well within the published rate limits.
- User-Agent: `reddit-digest/0.1 by u/<your_username>`

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials, never commit .env
python digest.py --sample   # test with bundled sample data, no API access needed
python digest.py            # real run, requires approved API access
```

The digest is written to `output/digest-YYYY-MM-DD.md`.

## Example output

```markdown
# Reddit digest, 2026-09-24

## r/LocalLLaMA

- [Sample post: running a small model on a laptop](https://www.reddit.com/r/LocalLLaMA/comments/example3/) (980 points, 150 comments, 16:13 UTC)
  > Placeholder body text for testing.

## r/investing

- [Sample thread: how do you think about long-term allocation?](https://www.reddit.com/r/investing/comments/example4/) (150 points, 203 comments, 17:13 UTC)
```

## Status

Early development. The digest logic is tested against `sample_data/posts.json`; the live API part will be enabled once Data API access is approved.
