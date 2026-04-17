import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.connection import init_schema
from app.db.seed import run_seed
from app.routers import transactions, reports


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_schema()
    if os.getenv("SEED_DB", "false").lower() == "true":
        run_seed()
    yield


app = FastAPI(title="Personal Finance Dashboard", lifespan=lifespan)

app.include_router(transactions.router)
app.include_router(reports.router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
