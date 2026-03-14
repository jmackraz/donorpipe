"""FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from donorpipe.api.auth import create_access_token, verify_password
from donorpipe.api.config import load_config
from donorpipe.api.graph_route import router


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    secret = os.environ.get("DONORPIPE_JWT_SECRET")
    if not secret:
        raise RuntimeError("DONORPIPE_JWT_SECRET environment variable is required")
    app.state.config = load_config()
    yield


app = FastAPI(title="DonorPipe", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://donorpipe.trickybit.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/help")
def get_help():
    path = Path(os.environ.get("DONORPIPE_HELP", "docs/help.md"))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Help file not found")
    return Response(content=path.read_text(), media_type="text/plain; charset=utf-8")


@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = app.state.config.users.get(form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(form.username, user.accounts)
    return {"access_token": token, "token_type": "bearer"}
