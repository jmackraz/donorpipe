"""Tests for ApiLoader."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from donorpipe.api.api_loader import ApiLoader
from donorpipe.api.app import app
from donorpipe.models.transaction_loader import TransactionLoader
from donorpipe.models.transaction_store import TransactionStore

TESTDATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "testdata"))


@pytest.fixture
def client(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"accounts": {"test_org": {"data_base": TESTDATA, "data_dirs": ["Stripe", "DonorBox", "QBO"]}}})
    )
    env_backup = os.environ.get("DONORPIPE_CONFIG")
    os.environ["DONORPIPE_CONFIG"] = str(config_file)
    with TestClient(app) as c:
        yield c
    if env_backup is None:
        os.environ.pop("DONORPIPE_CONFIG", None)
    else:
        os.environ["DONORPIPE_CONFIG"] = env_backup


def test_api_loader_unit():
    """Unit test: ApiLoader calls the right URL and deserializes the response."""
    fake_graph = {
        "donations": {"donorbox:1": {
            "id": "donorbox:1", "service": "donorbox", "tx_id": "1",
            "date": "2023-01-01", "net": 100.0, "currency": "USD",
            "name": "Alice", "payment_service": "stripe", "charge_tx_id": "ch_1",
            "designation": "General", "comment": "", "email": "alice@example.com",
            "charge_id": None, "receipt_ids": [],
        }},
        "charges": {},
        "payouts": {},
        "receipts": {},
    }
    mock_response = MagicMock()
    mock_response.json.return_value = fake_graph
    mock_response.raise_for_status.return_value = None

    with patch("httpx.get", return_value=mock_response) as mock_get:
        loader = ApiLoader("http://localhost:8000", "my_org")
        store = loader.load()

    mock_get.assert_called_once_with("http://localhost:8000/accounts/my_org/graph")
    assert isinstance(store, TransactionStore)
    assert "donorbox:1" in store.donations


def test_api_loader_strips_trailing_slash():
    """ApiLoader normalizes base_url by stripping trailing slashes."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"donations": {}, "charges": {}, "payouts": {}, "receipts": {}}
    mock_response.raise_for_status.return_value = None

    with patch("httpx.get", return_value=mock_response) as mock_get:
        loader = ApiLoader("http://localhost:8000/", "my_org")
        loader.load()

    mock_get.assert_called_once_with("http://localhost:8000/accounts/my_org/graph")


def test_api_loader_matches_csv_loader(client):
    """Integration test: ApiLoader and TransactionLoader produce identical graphs."""
    # CSV loader (same env setup the graph route uses)
    env_backup = os.environ.get("OSF_EXPORTS")
    os.environ["OSF_EXPORTS"] = TESTDATA
    try:
        csv_loader = TransactionLoader([], ["Stripe", "DonorBox", "QBO"])
        store_csv = csv_loader.load()
    finally:
        if env_backup is None:
            os.environ.pop("OSF_EXPORTS", None)
        else:
            os.environ["OSF_EXPORTS"] = env_backup
    graph_csv = store_csv.to_graph()

    # API loader — intercept httpx.get and forward to TestClient
    def fake_get(url: str):
        path = url.split("localhost:8000", 1)[-1]
        response = client.get(path)
        mock_resp = MagicMock()
        mock_resp.json.return_value = response.json()
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    with patch("httpx.get", side_effect=fake_get):
        api_loader = ApiLoader("http://localhost:8000", "test_org")
        store_api = api_loader.load()
    graph_api = store_api.to_graph()

    assert set(graph_csv["donations"].keys()) == set(graph_api["donations"].keys())
    assert set(graph_csv["charges"].keys()) == set(graph_api["charges"].keys())
    assert set(graph_csv["payouts"].keys()) == set(graph_api["payouts"].keys())
    assert set(graph_csv["receipts"].keys()) == set(graph_api["receipts"].keys())
