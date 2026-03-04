"""FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from donorpipe.api.config import load_config
from donorpipe.api.graph_route import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config = load_config()
    yield


app = FastAPI(title="DonorPipe", lifespan=lifespan)
app.include_router(router)
