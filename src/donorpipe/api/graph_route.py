"""GET /accounts/{account_id}/graph route."""

import json
import logging
from datetime import datetime
from email.utils import formatdate
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from donorpipe.api.auth import require_account_access
from donorpipe.api.config import UserConfig

logger = logging.getLogger(__name__)


def read_meta(path: Path) -> dict:
    """Read only the _meta object from the start of graph.json without loading the whole file."""
    chunk_size = 4096
    buffer = ""
    with open(path, encoding="utf-8") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            meta_key = buffer.find('"_meta"')
            if meta_key == -1:
                continue
            colon = buffer.find(":", meta_key)
            if colon == -1:
                continue
            obj_start = buffer.find("{", colon)
            if obj_start == -1:
                continue
            depth = 0
            for i, ch in enumerate(buffer[obj_start:], obj_start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return json.loads(buffer[obj_start : i + 1])
    return {}

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

    meta = read_meta(graph_path)
    generated_at = meta.get("generated_at")
    if generated_at:
        dt = datetime.fromisoformat(generated_at)
        response.headers["Last-Modified"] = formatdate(dt.timestamp(), usegmt=True)
