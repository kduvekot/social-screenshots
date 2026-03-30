# Truth Social Screenshot Generator

Generate shareable screenshot images of Truth Social posts. Scrapes post data
from [trumpstruth.org](https://trumpstruth.org) and renders a clean social-card
PNG that can be pasted into Twitter/X, Bluesky, group chats, etc.

## Quick start

```bash
# With uv (recommended) — dependencies install automatically:
uv run screenshot_post.py 37526

# Or install dependencies manually:
pip install requests beautifulsoup4 pillow
python screenshot_post.py 37526
```

## Rendering modes

| Mode | Command | Description |
|------|---------|-------------|
| **Default** | `uv run screenshot_post.py 37526` | Pure Python (Pillow). Cleanest output, no browser needed. |
| **Rodney** | `uv run screenshot_post.py --rodney 37526` | Headless Chrome screenshot of the archive page. |
| **Embed** | `uv run screenshot_post.py --embed 37526` | Official Truth Social embed screenshot. |

The `--rodney` and `--embed` modes require [rodney](https://github.com/simonw/rodney):
```bash
go install github.com/simonw/rodney@latest
```

## Output

Screenshots are saved as `truth_{id}.png` by default, or specify a custom path:
```bash
uv run screenshot_post.py 37526 my_screenshot.png
```

Committed screenshots live in `images/`.

## Avatar handling

Truth Social's CDN blocks non-residential IPs. The script uses a fallback chain:

1. `.avatar_cache/` (local download cache)
2. Local repo file (`454286ac07a6f6e6.jpeg`)
3. Embedded base64 avatar (built into the script)
4. "DJT" initials placeholder

## Fonts

The `fonts/` directory contains Inter (Regular and SemiBold), matching Truth
Social's actual typography. Falls back to DejaVu Sans if missing.
