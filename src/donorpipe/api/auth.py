"""JWT authentication for the DonorPipe API."""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserRecord(BaseModel):
    hashed_password: str
    accounts: list[str]


class UsersConfig(BaseModel):
    users: dict[str, UserRecord]


def load_users(path: str | None = None) -> UsersConfig:
    import json

    if path is None:
        path = os.environ.get("DONORPIPE_USERS_CONFIG", "users.json")
    with open(path) as f:
        return UsersConfig.model_validate(json.load(f))


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(username: str, accounts: list[str]) -> str:
    secret = os.environ["DONORPIPE_JWT_SECRET"]
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "accounts": accounts, "exp": expire}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    secret = os.environ["DONORPIPE_JWT_SECRET"]
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> UserRecord:
    payload = decode_token(token)
    username: str = payload.get("sub", "")
    users_config: UsersConfig = request.app.state.users
    user = users_config.users.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_account_access(
    account_id: str, user: UserRecord = Depends(get_current_user)
) -> UserRecord:
    if account_id not in user.accounts:
        raise HTTPException(status_code=403, detail="Access denied for this account")
    return user
