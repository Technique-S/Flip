"""Supported local deployment. Serve built assets and API on the same loopback socket."""

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import PlainTextResponse
from starlette.staticfiles import StaticFiles

from flip_api.app import app as api

DIST = Path(__file__).resolve().parents[4] / "apps/web/dist"


def application():
    if not (DIST / "index.html").is_file():
        raise RuntimeError("Build apps/web first with npm ci and npm run build.")
    local = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    local.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @local.middleware("http")
    async def local_browser(request: Request, call_next):
        origin = request.headers.get("origin")
        if not request.client or request.client.host not in ("127.0.0.1", "::1"):
            return PlainTextResponse("Loopback connections only.", 403)
        if origin and origin != str(request.base_url).rstrip("/"):
            return PlainTextResponse("Cross-origin access is disabled.", 403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return PlainTextResponse("Cross-site access is disabled.", 403)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    # Keep core API paths intact while serving the local application's static assets.
    for route in api.routes:
        if route.path.startswith("/api/") or route.path == "/healthz":
            local.router.routes.append(route)
    local.mount("/", StaticFiles(directory=DIST, html=True), name="workbench")
    return local


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    uvicorn.run(
        application(),
        host="127.0.0.1",
        port=parser.parse_args().port,
        proxy_headers=False,
        access_log=False,
    )
