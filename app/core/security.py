"""Optional workspace API authentication and server-controlled document access."""

import secrets

from fastapi import Header, HTTPException, Request


def authorize(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    expected = request.app.state.settings.technova_api_key
    if expected and not secrets.compare_digest((x_api_key or "").encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Enter your workspace API key to continue.")
