"""ApiLoader: loads a TransactionStore from the DonorPipe REST API."""

from __future__ import annotations

import httpx

from donorpipe.models.transaction_store import TransactionStore


class ApiLoader:
    def __init__(self, base_url: str, account_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.account_id = account_id

    def load(self) -> TransactionStore:
        url = f"{self.base_url}/accounts/{self.account_id}/graph"
        response = httpx.get(url)
        response.raise_for_status()
        return TransactionStore.from_graph(response.json())
