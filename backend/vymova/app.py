import argparse
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import settings
from .config import PORT

STATIC = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Vymova")
    app.include_router(settings.router)
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
