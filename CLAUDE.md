# Project: Truth Social Screenshot Generator

Single-script Python tool that generates shareable screenshot PNGs of Truth
Social posts by scraping trumpstruth.org.

## Key files

- `screenshot_post.py` — Main script. Uses PEP 723 inline metadata for uv.
- `fonts/` — Inter font files (matches Truth Social's typography).
- `454286ac07a6f6e6.jpeg` — Trump avatar fallback (CDN blocks datacenter IPs).
- `images/` — Committed screenshot PNGs.

## Running

```bash
uv run screenshot_post.py <post_id_or_url> [output.png]
uv run screenshot_post.py --rodney <id>   # headless Chrome via rodney
uv run screenshot_post.py --embed <id>    # official embed via rodney
```

## Architecture

- `fetch_post()` scrapes post data (name, handle, date, content, attachments)
- `render_post()` renders a Pillow-based social card with exact Truth Social colors/fonts
- `render_rodney()` / `render_embed()` use headless Chrome for browser-based screenshots
- Avatar loading has a multi-tier fallback chain (cache → local file → download → embedded base64 → initials)

## Development notes

- Dependencies: requests, beautifulsoup4, pillow (declared inline via PEP 723)
- The `.avatar_cache/` directory is gitignored — it's a runtime cache
- Root-level `truth_*.png` files are gitignored — use `images/` for committed screenshots
