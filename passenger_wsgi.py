"""
passenger_wsgi.py — cPanel Passenger entry point for Jiinue Loan Engine.
"""

import sys
import os
import io
import asyncio
import threading
from concurrent.futures import Future

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.main import app as fastapi_app




class ASGItoWSGI:
    def __init__(self, asgi_app):
        self.app = asgi_app

    def __call__(self, environ, start_response):
        response = {}
        body_parts = []

        async def run():
            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": environ["REQUEST_METHOD"].upper(),
                "headers": self._get_headers(environ),
                "path": environ.get("PATH_INFO", "/"),
                "query_string": environ.get("QUERY_STRING", "").encode("utf-8"),
                "root_path": environ.get("SCRIPT_NAME", ""),
                "scheme": environ.get("wsgi.url_scheme", "http"),
                "server": (
                    environ.get("SERVER_NAME", "localhost"),
                    int(environ.get("SERVER_PORT", 80)),
                ),
            }

            request_returned = False
            async def receive():
                nonlocal request_returned
                if not request_returned:
                    request_returned = True
                    try:
                        cl = int(environ.get("CONTENT_LENGTH", 0))
                    except (ValueError, TypeError):
                        cl = 0
                    
                    if cl > 0:
                        body = environ["wsgi.input"].read(cl)
                    else:
                        body = b""
                        
                    return {"type": "http.request", "body": body, "more_body": False}
                return {"type": "http.disconnect"}

            async def send(message):
                if message["type"] == "http.response.start":
                    response["status"] = message["status"]
                    headers = []
                    for k, v in message.get("headers", []):
                        key = k.decode("latin-1", errors="replace").lower()
                        val = v.decode("latin-1", errors="replace")
                        headers.append((key, val))
                    response["headers"] = headers
                elif message["type"] == "http.response.body":
                    chunk = message.get("body", b"")
                    if chunk:
                        body_parts.append(chunk)

            await self.app(scope, receive, send)

        try:
            asyncio.run(run())
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
            return [f"Error: {e}\n{tb}".encode("utf-8", errors="replace")]

        status_code = response.get("status", 500)
        from http.client import responses as http_responses
        status_str = f"{status_code} {http_responses.get(status_code, 'Unknown')}"
        start_response(status_str, response.get("headers", []))
        return body_parts if body_parts else []

    def _get_headers(self, environ):
        headers = []
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                name = key[5:].replace("_", "-").lower().encode("latin-1", errors="replace")
                headers.append((name, value.encode("latin-1", errors="replace")))
            elif key == "CONTENT_TYPE" and value:
                headers.append((b"content-type", value.encode("latin-1", errors="replace")))
            elif key == "CONTENT_LENGTH" and value:
                headers.append((b"content-length", value.encode("latin-1", errors="replace")))
        return headers


application = ASGItoWSGI(fastapi_app)
