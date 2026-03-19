"""POST/GET /accounts/{account_id}/refresh — bookkeeper-triggered refresh."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from donorpipe.api.auth import require_account_access
from donorpipe.api.config import UserConfig
from donorpipe.api.graph_route import read_meta

logger = logging.getLogger(__name__)

router = APIRouter()


def _state_path(data_base: str) -> Path:
    return Path(data_base).resolve() / "refresh_state.json"


def _graph_path(data_base: str) -> Path:
    return Path(data_base).resolve() / "graph.json"


@router.post("/accounts/{account_id}/refresh")
def request_refresh(
    account_id: str,
    request: Request,
    _user: UserConfig = Depends(require_account_access),
) -> dict:
    config = request.app.state.config
    account = config.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")

    requested_at = datetime.now(timezone.utc).isoformat()
    state = {"requested_at": requested_at}
    try:
        _state_path(account.data_base).write_text(json.dumps(state, indent=2))
    except OSError as e:
        logger.error("Failed to write refresh_state.json for '%s': %s", account_id, e)
        raise HTTPException(status_code=500, detail="Could not record refresh request")

    return {"status": "requested", "requested_at": requested_at}


@router.get("/accounts/{account_id}/refresh")
def get_refresh_status(
    account_id: str,
    request: Request,
    _user: UserConfig = Depends(require_account_access),
) -> dict:
    config = request.app.state.config
    account = config.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")

    state_file = _state_path(account.data_base)
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            requested_at: str | None = state.get("requested_at")
        except (OSError, json.JSONDecodeError):
            requested_at = None
    else:
        requested_at = None

    graph_file = _graph_path(account.data_base)
    if graph_file.exists():
        meta = read_meta(graph_file)
        last_updated: str | None = meta.get("generated_at")
    else:
        last_updated = None

    pending = bool(
        requested_at and (not last_updated or last_updated < requested_at)
    )

    return {
        "pending": pending,
        "requested_at": requested_at,
        "last_updated": last_updated,
    }
