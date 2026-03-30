"""Vercel serverless function — returns a Truth Social post screenshot as PNG."""

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root so we can import the main script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import screenshot_post  # noqa: E402

# Writable tmp dir for serverless environment
screenshot_post.AVATAR_CACHE = "/tmp/.avatar_cache"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        url = params.get("url", [None])[0]
        post_id = params.get("id", [None])[0]

        if not url and not post_id:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Missing ?url= or ?id= parameter")
            return

        try:
            post = screenshot_post.fetch_post(url or post_id)
            output_path = f"/tmp/truth_{post['post_id']}.png"
            screenshot_post.render_post(post, output_path)

            with open(output_path, "rb") as f:
                png_data = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "public, max-age=86400, s-maxage=86400")
            self.end_headers()
            self.wfile.write(png_data)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())
