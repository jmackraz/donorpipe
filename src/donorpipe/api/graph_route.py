"""GET /accounts/{account_id}/graph route."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from donorpipe.api.auth import require_account_access
from donorpipe.api.config import UserConfig

router = APIRouter()


@router.get("/accounts/{account_id}/graph")
def get_graph(
    account_id: str,
    request: Request,
    _user: UserConfig = Depends(require_account_access),
) -> dict:
    config = request.app.state.config
    account = config.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")

    graph_path = Path(account.data_base).resolve() / "graph.json"
    if not graph_path.exists():
        raise HTTPException(status_code=503, detail=f"Graph not built for account '{account_id}'")

    with open(graph_path) as f:
        return json.load(f)
