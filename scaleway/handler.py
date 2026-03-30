"""Scaleway Serverless Function — returns a Truth Social post screenshot as PNG."""

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import screenshot_post  # noqa: E402

screenshot_post.AVATAR_CACHE = "/tmp/.avatar_cache"


def handle(event, context):
    qs = event.get("queryStringParameters") or {}
    url = qs.get("url")
    post_id = qs.get("id")

    if not url and not post_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "text/plain"},
            "body": "Missing ?url= or ?id= parameter",
        }

    try:
        post = screenshot_post.fetch_post(url or post_id)
        output_path = f"/tmp/truth_{post['post_id']}.png"
        screenshot_post.render_post(post, output_path)

        with open(output_path, "rb") as f:
            png_data = f.read()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "image/png",
                "Cache-Control": "public, max-age=86400",
            },
            "body": base64.b64encode(png_data).decode(),
            "isBase64Encoded": True,
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/plain"},
            "body": f"Error: {e}",
        }
