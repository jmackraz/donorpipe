"""GET /accounts/{account_id}/graph route."""

import os

from fastapi import APIRouter, Depends, HTTPException, Request

from donorpipe.api.auth import require_account_access
from donorpipe.api.config import UserConfig
from donorpipe.models.transaction_loader import TransactionLoader

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

    data_base = os.path.abspath(account.data_base)
    env_backup = os.environ.get("OSF_EXPORTS")
    os.environ["OSF_EXPORTS"] = data_base
    try:
        loader = TransactionLoader([], account.data_dirs)
        store = loader.load()
    finally:
        if env_backup is None:
            os.environ.pop("OSF_EXPORTS", None)
        else:
            os.environ["OSF_EXPORTS"] = env_backup

    return store.to_graph()
