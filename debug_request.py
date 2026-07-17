import sys
import os
import io
import asyncio
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.main import app as fastapi_app

response = {}
body_parts = []

async def run():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "headers": [],
        "path": "/",
        "query_string": b"",
        "root_path": "",
        "scheme": "https",
        "server": ("jiinueloan.pssl.co.ke", 443),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
        elif message["type"] == "http.response.body":
            body_parts.append(message.get("body", b""))

    await fastapi_app(scope, receive, send)

try:
    asyncio.run(run())
    print(f"Status: {response.get('status')}")
    body = b"".join(body_parts)
    print(f"Body ({len(body)} bytes): {body[:300]}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
