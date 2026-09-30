"""FastAPI entry point.  Run:  uvicorn app.main:app --reload"""
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import config
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
config.ensure_dirs()

app = FastAPI(title="ComicCraft - AI Comic Story Creator", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.include_router(router)
