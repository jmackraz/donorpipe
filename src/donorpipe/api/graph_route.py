"""GET /accounts/{account_id}/graph route."""

import json
import logging
from datetime import datetime
from email.utils import formatdate
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from donorpipe.api.auth import require_account_access
from donorpipe.api.config import UserConfig

router = APIRouter()


@router.get("/accounts/{account_id}/graph")
def get_graph(
    account_id: str,
    request: Request,
    response: Response,
    _user: UserConfig = Depends(require_account_access),
) -> dict:
    config = request.app.state.config
    account = config.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")

    graph_path = Path(account.data_base).resolve() / "graph.json"
    if not graph_path.exists():
        logger.warning("Graph not found for account '%s': %s", account_id, graph_path)
        raise HTTPException(status_code=503, detail=f"Graph not built for account '{account_id}'")

    with open(graph_path) as f:
        graph = json.load(f)

    generated_at = graph.get("_meta", {}).get("generated_at")
    if generated_at:
        dt = datetime.fromisoformat(generated_at)
        response.headers["Last-Modified"] = formatdate(dt.timestamp(), usegmt=True)

    return graph


@router.head("/accounts/{account_id}/graph")
def head_graph(
    account_id: str,
    request: Request,
    response: Response,
    _user: UserConfig = Depends(require_account_access),
) -> None:
    config = request.app.state.config
    account = config.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")

    graph_path = Path(account.data_base).resolve() / "graph.json"
    if not graph_path.exists():
        raise HTTPException(status_code=503, detail=f"Graph not built for account '{account_id}'")

    # TODO: loading the full graph just to read _meta.generated_at is wasteful.
    # Optimize by reading only the first few KB of the file (_meta is always
    # written at the top of graph.json by generate_graph_json.py).
    with open(graph_path) as f:
        graph = json.load(f)

    generated_at = graph.get("_meta", {}).get("generated_at")
    if generated_at:
        dt = datetime.fromisoformat(generated_at)
        response.headers["Last-Modified"] = formatdate(dt.timestamp(), usegmt=True)
