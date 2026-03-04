"""API integration tests for the graph route."""

import os

import pytest
from fastapi.testclient import TestClient

from donorpipe.api.app import app

TESTDATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "testdata"))


@pytest.fixture
def client(tmp_path):
    import json

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


def test_get_graph_returns_200(client):
    response = client.get("/accounts/test_org/graph")
    assert response.status_code == 200


def test_get_graph_has_required_keys(client):
    response = client.get("/accounts/test_org/graph")
    data = response.json()
    assert set(data.keys()) >= {"donations", "charges", "payouts", "receipts"}


def test_get_graph_entities_nonempty(client):
    response = client.get("/accounts/test_org/graph")
    data = response.json()
    assert len(data["donations"]) > 0
    assert len(data["charges"]) > 0
    assert len(data["payouts"]) > 0


def test_get_graph_unknown_account_returns_404(client):
    response = client.get("/accounts/unknown/graph")
    assert response.status_code == 404
