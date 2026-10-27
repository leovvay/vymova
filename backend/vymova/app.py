import argparse
import logging
import re
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager

from . import info, lessons, settings
from .lessons import steps
from .config import PORT

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    steps.register_all()
    lessons.runner.start()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Vymova", lifespan=_lifespan)
    # программа только для этого компьютера: чужие сайты не могут ни читать её, ни запускать платные шаги
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

    @app.middleware("http")
    async def same_origin_only(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin and \
                not re.fullmatch(r"http://(localhost|127\.0\.0\.1)(:\d+)?", origin):
            return JSONResponse({"detail": "Запрос не с этого компьютера"}, status_code=403)
        return await call_next(request)

    app.include_router(settings.router)
    app.include_router(lessons.router)
    app.include_router(info.router)
    if STATIC.exists():
        app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
    return app


def main() -> None:
    ap = argparse.ArgumentParser(prog="vymova")
    sub = ap.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=PORT)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(create_app(), host=args.host, port=args.port)
