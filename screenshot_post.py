#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "beautifulsoup4",
#     "pillow",
# ]
# ///
"""
Generate shareable screenshot images of Truth Social posts.

Scrapes post data from trumpstruth.org and renders a clean social-card
PNG image that can be pasted into Twitter, Bluesky, group chats, etc.

Requires the Inter font files in ./fonts/ for best results (falls back
to DejaVu Sans). The --rodney and --embed modes require the rodney CLI
(go install github.com/simonw/rodney@latest).
"""

import argparse
import sys
import os
import re
import subprocess
import shutil
import base64
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AVATAR_CACHE = os.path.join(SCRIPT_DIR, ".avatar_cache")

# Trump's Truth Social avatar (120x120 JPEG), embedded to avoid CDN dependency.
# Truth Social's CDN (static-assets-1.truthsocial.com) returns 403 for datacenter IPs.
_EMBEDDED_AVATAR_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQ"
    "FxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMK"
    "ChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKC"
    "goKCj/wAARCAB4AHgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcI"
    "CQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0Kx"
    "wRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZn"
    "aGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
    "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAA"
    "AAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdh"
    "cRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK"
    "U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmq"
    "srO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMB"
    "AAIRAxEAPwD57wRzWpp9wqxmCcDyX5DHoDW98MfC1p4t8UxaZeXy2qujtjnfIQpwF4xk"
    "HBIPbOKl1nw1d+GtQm02+ktTdRgF1gmEgB9/7p74PPNehgaPtJWucOMqcsL2M63kgYiJ"
    "3EUxG3Mg3RyDtnHf3q1p0raReBZIy0DHd5W4B0/2o2PDL7H9OtWLS3jlsiJ4kkQ8Fccg"
    "1v6JY2M9v9muJkmtWHyRyDOD6jvn2r1fq9S6cWeLLFU1dSWh0HhfUdO1G3ltTFGk4O8O"
    "FwCfU9wfz/KtvwlYLqHimSxWEhEhZmgY8AjHIHbjoVODXNeFPCmjf8JLbw3upXNvDK3l"
    "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"
)


def fetch_post(url_or_id):
    """Scrape post data from trumpstruth.org."""
    if str(url_or_id).isdigit():
        url = f"https://trumpstruth.org/statuses/{url_or_id}"
    else:
        url = url_or_id

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    name_el = soup.select_one(".status-info__account-name")
    meta_items = soup.select(".status-info__meta-item")
    content_el = soup.select_one(".status__content")
    avatar_el = soup.select_one(".status-info__avatar")

    name = name_el.get_text(strip=True) if name_el else "Unknown"
    handle = meta_items[0].get_text(strip=True) if len(meta_items) > 0 else ""
    date = meta_items[1].get_text(strip=True) if len(meta_items) > 1 else ""
    avatar_url = avatar_el["src"] if avatar_el and avatar_el.get("src") else None

    # Extract content preserving line breaks (<br/> tags)
    content = ""
    if content_el:
        # Replace <br/> tags with newlines before extracting text
        for br in content_el.find_all("br"):
            br.replace_with("\n")
        content = content_el.get_text()
        # Clean up: collapse multiple spaces, preserve paragraph breaks
        lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            lines.append(stripped)
        content = "\n".join(lines)
        # Collapse 3+ newlines into 2 (paragraph break)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()

    # Extract attached images
    attachments = []
    for att in soup.select(".status-attachment--image img"):
        src = att.get("src", "")
        if src:
            attachments.append(src)

    # Extract Truth Social original URL for embed mode
    ts_link = soup.select_one(".status__external-link")
    ts_url = ts_link["href"] if ts_link and ts_link.get("href") else None

    match = re.search(r"/statuses/(\d+)", url)
    post_id = match.group(1) if match else ""

    return {
        "name": name,
        "handle": handle,
        "date": date,
        "content": content,
        "avatar_url": avatar_url,
        "attachments": attachments,
        "ts_url": ts_url,
        "url": url,
        "post_id": post_id,
    }


def load_avatar(url, size=64):
    """Download avatar, with local cache fallback."""
    os.makedirs(AVATAR_CACHE, exist_ok=True)

    # Derive cache filename from URL
    cache_name = re.sub(r"[^a-zA-Z0-9]", "_", url.split("/")[-1]) + ".png"
    cache_path = os.path.join(AVATAR_CACHE, cache_name)

    img = None

    # Try cached version first
    if os.path.exists(cache_path):
        try:
            img = Image.open(cache_path).convert("RGBA")
        except Exception:
            pass

    # Try local file in repo (e.g. 454286ac07a6f6e6.jpeg committed to repo)
    if img is None:
        local_name = url.split("/")[-1]  # e.g. "454286ac07a6f6e6.jpeg"
        local_path = os.path.join(SCRIPT_DIR, local_name)
        if os.path.exists(local_path):
            try:
                img = Image.open(local_path).convert("RGBA")
                img.save(cache_path)  # cache for next time
            except Exception:
                pass

    # Try downloading
    if img is None:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            # Cache it for next time
            img.save(cache_path)
        except Exception:
            pass

    # Fall back to embedded avatar (works without any external files)
    if img is None and _EMBEDDED_AVATAR_B64:
        try:
            img = Image.open(BytesIO(base64.b64decode(_EMBEDDED_AVATAR_B64))).convert("RGBA")
        except Exception:
            pass

    if img is not None:
        img = img.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)
        img.putalpha(mask)
        return img

    # Generate initials placeholder
    return _make_initials_avatar(size)


def _make_initials_avatar(size, initials="DJT"):
    """Generate a circular avatar with initials as fallback."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Dark blue circle
    draw.ellipse((0, 0, size - 1, size - 1), fill=(30, 60, 114))
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            int(size * 0.38),
        )
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2, (size - th) / 2 - bbox[1]),
        initials,
        fill=(255, 255, 255),
        font=font,
    )
    return img


def wrap_text(text, font, max_width, draw):
    """Word-wrap text to fit within max_width pixels."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current_line = words[0]
        for word in words[1:]:
            test = current_line + " " + word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
    return lines


def download_image(url):
    """Download an image from a URL, return PIL Image or None."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception:
        return None


def _draw_verified_badge(draw, x, y, size=16):
    """Draw Truth Social verified checkmark badge (blue circle with white check)."""
    # Blue circle background (Truth Social's secondary-500 indigo)
    badge_color = (99, 102, 241)  # indigo-500 / #6366f1
    cx, cy = x + size // 2, y + size // 2
    r = size // 2
    draw.ellipse((x, y, x + size, y + size), fill=badge_color)
    # White checkmark
    s = size / 16  # scale factor
    check_points = [
        (x + 4 * s, y + 8 * s),
        (x + 7 * s, y + 11 * s),
        (x + 12 * s, y + 5 * s),
    ]
    draw.line(check_points[:2], fill=(255, 255, 255), width=max(1, int(1.8 * s)))
    draw.line(check_points[1:], fill=(255, 255, 255), width=max(1, int(1.8 * s)))



def render_post(post, output_path):
    """Render post as a styled social card inspired by Truth Social."""
    outer_padding = 28
    card_width = 620
    card_padding_x = 36
    card_padding_top = 30
    card_padding_bottom = 36
    content_width = card_width - card_padding_x * 2
    avatar_size = 60
    avatar_gap = 16
    total_width = card_width + outer_padding * 2

    # Colors from Truth Social (exact RGB values)
    outer_bg = (240, 240, 240)
    card_bg = (255, 255, 255)
    name_color = (8, 5, 27)        # rgb(8, 5, 27)
    meta_color = (101, 97, 117)    # rgb(101, 97, 117)
    text_color = (8, 5, 27)        # rgb(8, 5, 27)
    border_color = (215, 215, 215)
    separator_color = (230, 230, 230)

    # Inter font (same as Truth Social) with fallback to DejaVu
    fonts_dir = os.path.join(SCRIPT_DIR, "fonts")
    try:
        font_name = ImageFont.truetype(os.path.join(fonts_dir, "Inter-SemiBold.ttf"), 18)
        font_handle = ImageFont.truetype(os.path.join(fonts_dir, "Inter-Regular.ttf"), 15)
        font_body = ImageFont.truetype(os.path.join(fonts_dir, "Inter-Regular.ttf"), 20)
    except OSError:
        try:
            font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            font_handle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
            font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except OSError:
            font_name = ImageFont.load_default()
            font_handle = font_name
            font_body = font_name

    # Measure text using temporary canvas
    tmp = Image.new("RGB", (card_width, 100))
    tmp_draw = ImageDraw.Draw(tmp)

    # Name width (for badge placement)
    name_bbox = tmp_draw.textbbox((0, 0), post["name"], font=font_name)
    name_w = name_bbox[2] - name_bbox[0]

    handle_text = post["handle"]
    meta_text = f"{handle_text} \u00b7 {post['date']}"
    meta_lines = wrap_text(meta_text, font_handle, content_width - avatar_size - avatar_gap, tmp_draw)
    meta_line_height = 20
    meta_height = len(meta_lines) * meta_line_height

    body_lines = wrap_text(post["content"], font_body, content_width, tmp_draw)
    body_line_height = 30
    body_height = len(body_lines) * body_line_height

    # Download attachments
    attachment_images = []
    attachment_total_height = 0
    for att_url in post.get("attachments", []):
        att_img = download_image(att_url)
        if att_img:
            scale = content_width / att_img.width
            att_h = int(att_img.height * scale)
            att_img = att_img.resize((content_width, att_h), Image.LANCZOS)
            attachment_images.append(att_img)
            attachment_total_height += att_h + 16

    name_height = 24
    header_height = max(avatar_size, name_height + meta_height + 4)
    separator_spacing = 20

    card_height = (
        card_padding_top
        + header_height
        + separator_spacing
        + 1
        + separator_spacing
        + body_height
        + attachment_total_height
        + card_padding_bottom
    )
    total_height = card_height + outer_padding * 2

    img = Image.new("RGB", (total_width, total_height), outer_bg)
    draw = ImageDraw.Draw(img)

    card_x = outer_padding
    card_y = outer_padding
    draw.rounded_rectangle(
        [(card_x, card_y), (card_x + card_width - 1, card_y + card_height - 1)],
        radius=12,
        fill=card_bg,
        outline=border_color,
        width=1,
    )

    # --- Header: Avatar + Name + Badge + Handle ---
    ax = card_x + card_padding_x
    ay = card_y + card_padding_top
    avatar = load_avatar(post["avatar_url"], avatar_size) if post["avatar_url"] else _make_initials_avatar(avatar_size)
    if avatar:
        img.paste(avatar, (ax, ay), avatar)

    text_x = ax + avatar_size + avatar_gap
    text_y = ay + 2
    draw.text((text_x, text_y), post["name"], fill=name_color, font=font_name)

    # Verified badge right after name
    badge_size = 20
    badge_x = text_x + name_w + 5
    badge_y = text_y + (name_height - badge_size) // 2
    _draw_verified_badge(draw, badge_x, badge_y, badge_size)

    # Handle + date
    meta_y = text_y + name_height
    for mline in meta_lines:
        draw.text((text_x, meta_y), mline, fill=meta_color, font=font_handle)
        meta_y += meta_line_height

    # Separator
    sep_y = ay + header_height + separator_spacing
    draw.line(
        [(card_x + card_padding_x, sep_y), (card_x + card_width - card_padding_x, sep_y)],
        fill=separator_color,
        width=1,
    )

    # Body text
    body_y = sep_y + separator_spacing
    for line in body_lines:
        draw.text((card_x + card_padding_x, body_y), line, fill=text_color, font=font_body)
        body_y += body_line_height

    # Attached images
    for att_img in attachment_images:
        body_y += 16
        img.paste(att_img, (card_x + card_padding_x, body_y))
        body_y += att_img.height

    img.save(output_path, "PNG", quality=95)
    return output_path


def render_rodney(post, output_path):
    """Use headless Chrome (rodney) for pixel-perfect screenshot."""
    rodney = shutil.which("rodney")
    if not rodney:
        gopath = subprocess.run(["go", "env", "GOPATH"], capture_output=True, text=True).stdout.strip()
        rodney = os.path.join(gopath, "bin", "rodney")
    if not os.path.exists(rodney):
        print("Error: rodney not found. Install with: go install github.com/simonw/rodney@latest")
        sys.exit(1)

    def rod(*args):
        result = subprocess.run([rodney, *args], capture_output=True, text=True, timeout=30)
        if result.returncode != 0 and "unknown command" not in result.stderr:
            print(f"  rodney {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout.strip()

    # Check if rodney is running
    status = rod("status")
    if "not running" in status.lower() or "no browser" in status.lower():
        print("  Starting Chrome...")
        rod("start")

    print("  Opening page...")
    rod("open", post["url"])
    rod("waitidle")

    # Fix broken avatar by replacing with a data URI fallback
    # Generate a small avatar and convert to base64
    avatar_img = load_avatar(post["avatar_url"], 120) if post["avatar_url"] else _make_initials_avatar(120)
    buf = BytesIO()
    avatar_img.save(buf, format="PNG")
    avatar_b64 = base64.b64encode(buf.getvalue()).decode()

    rod("js", f'''
        (function() {{
            var img = document.querySelector('.status-info__avatar');
            if (img && (img.naturalWidth === 0 || img.complete === false)) {{
                img.src = 'data:image/png;base64,{avatar_b64}';
            }}
            // Also try to fix if it loaded but is broken
            var imgs = document.querySelectorAll('.status-info__avatar');
            imgs.forEach(function(i) {{
                if (!i.complete || i.naturalWidth === 0) {{
                    i.src = 'data:image/png;base64,{avatar_b64}';
                }}
            }});
            // Hide "Original Post" link for cleaner screenshot
            var ext = document.querySelector('.status__external-link');
            if (ext) ext.style.display = 'none';
        }})()
    ''')

    # Wait a moment for the image to render
    rod("sleep", "1")

    print("  Taking screenshot...")
    rod("screenshot-el", ".status", output_path)
    return output_path


def render_embed(post, output_path):
    """Screenshot the official Truth Social embed via rodney."""
    if not post.get("ts_url"):
        print("Error: no Truth Social URL found for this post")
        sys.exit(1)

    embed_url = post["ts_url"] + "/embed"

    rodney = shutil.which("rodney")
    if not rodney:
        gopath = subprocess.run(["go", "env", "GOPATH"], capture_output=True, text=True).stdout.strip()
        rodney = os.path.join(gopath, "bin", "rodney")
    if not os.path.exists(rodney):
        print("Error: rodney not found. Install with: go install github.com/simonw/rodney@latest")
        sys.exit(1)

    def rod(*args):
        result = subprocess.run([rodney, *args], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            if "unknown command" not in result.stderr:
                print(f"  rodney {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout.strip()

    status = rod("status")
    if "not running" in status.lower() or "no browser" in status.lower():
        print("  Starting Chrome...")
        rod("start")

    print(f"  Opening embed: {embed_url}")
    rod("open", embed_url)
    rod("sleep", "4")
    rod("waitidle")

    # Dismiss cookie banner via JS (don't click - it can navigate away)
    rod("js", "(function(){ var c = document.getElementById('cookiescript_injected'); if(c) c.remove(); var o = document.getElementById('cookiescript_overlay'); if(o) o.remove(); return 'done'; })()")

    # Remove text truncation (max-h-40 overflow-hidden) and hide Show More
    rod("js", "(function(){ var el = document.querySelector('[data-testid=\"status-content\"] p[data-markup]'); if(el){ el.style.maxHeight = 'none'; el.style.overflow = 'visible'; } return el ? 'untruncated' : 'no content found'; })()")
    rod("js", "(function(){ var all = document.querySelectorAll('*'); all.forEach(function(e){ if(e.children.length === 0 && e.textContent.trim() === 'Show More') e.closest('div').style.display = 'none'; }); return 'done'; })()")

    # Inject real avatar if available
    avatar_img = load_avatar(post["avatar_url"], 120) if post["avatar_url"] else _make_initials_avatar(120)
    buf = BytesIO()
    avatar_img.save(buf, format="PNG")
    avatar_b64 = base64.b64encode(buf.getvalue()).decode()

    rod("js", f"(function(){{ var container = document.querySelector('[data-testid=\"account\"] a div.flex.items-center'); if(container){{ container.innerHTML = '<img src=\"data:image/png;base64,{avatar_b64}\" style=\"width:42px;height:42px;border-radius:50%\" />'; }} return container ? 'avatar injected' : 'no avatar container'; }})()")

    rod("sleep", "1")

    # Screenshot at 600px width
    print("  Taking screenshot...")
    rod("screenshot", "-w", "600", output_path)

    # Crop out excess whitespace below the post
    try:
        img = Image.open(output_path)
        # Find the bottom of content (last non-white row)
        import numpy as np
        arr = np.array(img)
        # Find rows that aren't all white (255,255,255)
        non_white = np.any(arr < 250, axis=(1, 2))
        if non_white.any():
            last_row = np.max(np.where(non_white)) + 20  # 20px padding
            img = img.crop((0, 0, img.width, min(last_row, img.height)))
            img.save(output_path)
    except ImportError:
        pass  # numpy not available, skip cropping

    return output_path


def main():
    parser = argparse.ArgumentParser(
        prog="screenshot_post.py",
        description="Generate shareable screenshot images of Truth Social posts.",
        epilog="""examples:
  uv run screenshot_post.py 37268
  uv run screenshot_post.py https://trumpstruth.org/statuses/37268
  uv run screenshot_post.py --rodney 37268 my_screenshot.png
  uv run screenshot_post.py --embed 37268

rendering modes:
  Default (Pillow) renders a styled card entirely in Python - no browser
  needed. Uses the Inter font (same as Truth Social) with exact colors
  extracted from the site. This produces the cleanest output.

  --rodney screenshots the trumpstruth.org archive page using headless
  Chrome. Automatically injects the avatar (CDN blocks datacenter IPs).

  --embed screenshots Truth Social's official embed page. Removes text
  truncation, cookie banners, and injects the avatar. Closest to the
  original but requires rodney and looks slightly "squeezed" due to
  browser font smoothing.

install:
  pip install requests beautifulsoup4 pillow   # or let uv handle it
  go install github.com/simonw/rodney@latest   # only for --rodney/--embed

  With uv installed, just run the script directly - dependencies are
  declared inline (PEP 723) and installed automatically:
    uv run screenshot_post.py 37268

avatar:
  Truth Social's CDN blocks non-residential IPs. The script uses a
  fallback chain: .avatar_cache/ -> local repo file -> download ->
  "DJT" initials placeholder. To ensure the avatar works, place the
  avatar image file (e.g. 454286ac07a6f6e6.jpeg) in the script directory.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--rodney",
        action="store_true",
        help="screenshot trumpstruth.org via headless Chrome (needs rodney)",
    )
    mode_group.add_argument(
        "--embed",
        action="store_true",
        help="screenshot the official Truth Social embed (needs rodney)",
    )

    parser.add_argument(
        "url_or_id",
        help="trumpstruth.org URL or numeric post ID (e.g. 37268)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="output PNG filename (default: truth_{id}.png)",
    )

    args = parser.parse_args()

    print("Fetching post...")
    post = fetch_post(args.url_or_id)
    print(f"  Author: {post['name']} ({post['handle']})")
    print(f"  Date:   {post['date']}")
    print(f"  Length: {len(post['content'])} chars")

    output = args.output or f"truth_{post['post_id']}.png"

    if args.embed:
        print("Rendering via Truth Social embed...")
        path = render_embed(post, output)
    elif args.rodney:
        print("Rendering with rodney (headless Chrome)...")
        path = render_rodney(post, output)
    else:
        print("Rendering image...")
        path = render_post(post, output)

    print(f"Saved: {path}")


if __name__ == "__main__":
    main()
