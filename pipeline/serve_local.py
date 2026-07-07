"""Serve /api/contract locally for end-to-end dev (Vercel serves api/contract.py in prod)."""

from http.server import HTTPServer

from api.contract import handler

if __name__ == "__main__":
    print("serving contract on http://localhost:8000/api/contract")  # noqa: T201
    HTTPServer(("127.0.0.1", 8000), handler).serve_forever()
