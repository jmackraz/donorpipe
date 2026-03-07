"""FastAPI application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from donorpipe.api.auth import create_access_token, load_users, verify_password
from donorpipe.api.config import load_config
from donorpipe.api.graph_route import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    secret = os.environ.get("DONORPIPE_JWT_SECRET")
    if not secret:
        raise RuntimeError("DONORPIPE_JWT_SECRET environment variable is required")
    app.state.config = load_config()
    app.state.users = load_users()
    yield


app = FastAPI(title="DonorPipe", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)


@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    users_config = app.state.users
    user = users_config.users.get(form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(form.username, user.accounts)
    return {"access_token": token, "token_type": "bearer"}
