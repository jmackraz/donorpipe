"""API integration tests for the graph route."""

import json
import os

import bcrypt
import pytest
from fastapi.testclient import TestClient

from donorpipe.api.app import app
from donorpipe.api.auth import create_access_token

TESTDATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "testdata"))
TEST_SECRET = "test-secret-key-for-pytest"


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture
def client(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "accounts": {
                    "test_org": {
                        "data_base": TESTDATA,
                        "data_dirs": ["Stripe", "DonorBox", "QBO"],
                    }
                },
                "users": {
                    "alice": {
                        "hashed_password": _make_hash("testpass"),
                        # alice has test_org + nonexistent (for 404 test)
                        "accounts": ["test_org", "nonexistent"],
                    }
                },
            }
        )
    )

    env_backup = {k: os.environ.get(k) for k in ("DONORPIPE_CONFIG", "DONORPIPE_JWT_SECRET")}
    os.environ["DONORPIPE_CONFIG"] = str(config_file)
    os.environ["DONORPIPE_JWT_SECRET"] = TEST_SECRET

    with TestClient(app) as c:
        yield c

    for k, v in env_backup.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def auth_headers() -> dict:
    os.environ["DONORPIPE_JWT_SECRET"] = TEST_SECRET
    token = create_access_token("alice", ["test_org", "nonexistent"])
    return {"Authorization": f"Bearer {token}"}


def test_get_graph_returns_200(client, auth_headers):
    response = client.get("/accounts/test_org/graph", headers=auth_headers)
    assert response.status_code == 200


def test_get_graph_has_required_keys(client, auth_headers):
    response = client.get("/accounts/test_org/graph", headers=auth_headers)
    data = response.json()
    assert set(data.keys()) >= {"donations", "charges", "payouts", "receipts"}


def test_get_graph_entities_nonempty(client, auth_headers):
    response = client.get("/accounts/test_org/graph", headers=auth_headers)
    data = response.json()
    assert len(data["donations"]) > 0
    assert len(data["charges"]) > 0
    assert len(data["payouts"]) > 0


def test_get_graph_unknown_account_returns_404(client, auth_headers):
    # Alice has "nonexistent" in her accounts but it's not in config → 404
    response = client.get("/accounts/nonexistent/graph", headers=auth_headers)
    assert response.status_code == 404
