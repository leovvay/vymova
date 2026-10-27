import argparse
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager

from . import lessons, settings
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
    app.include_router(settings.router)
    app.include_router(lessons.router)
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
