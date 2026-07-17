import sys
import os
import asyncio
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.main import app as fastapi_app

body = b"name=DebugTestMember999&phone=0799999999&savings_balance=500"

async def run():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "headers": [
            (b"content-type", b"application/x-www-form-urlencoded"),
            (b"content-length", str(len(body)).encode()),
        ],
        "path": "/members/new",
        "query_string": b"",
        "root_path": "",
        "scheme": "https",
        "server": ("jiinueloan.pssl.co.ke", 443),
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    response = {}
    body_parts = []

    async def send(message):
        if message["type"] == "http.response.start":
            response["status"] = message["status"]
        elif message["type"] == "http.response.body":
            body_parts.append(message.get("body", b""))

    await fastapi_app(scope, receive, send)
    full_body = b"".join(body_parts).decode(errors="replace")
    print(f"Status: {response.get('status')}")

    import re
    match = re.search(r'alert-danger[^>]*>.*?<[^/]', full_body, re.DOTALL)
    if match:
        print(f"Error block: {match.group()[:500]}")
    else:
        # print last 500 chars which often has the error
        print(f"Body tail: {full_body[-500:]}")

try:
    asyncio.run(run())
except Exception as e:
    traceback.print_exc()
