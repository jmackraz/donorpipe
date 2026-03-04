"""FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from donorpipe.api.config import load_config
from donorpipe.api.graph_route import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config = load_config()
    yield


app = FastAPI(title="DonorPipe", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)
