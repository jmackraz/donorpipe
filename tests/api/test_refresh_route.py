"""API integration tests for the refresh route."""

import json
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from fastapi.testclient import TestClient

from donorpipe.api.app import app
from donorpipe.api.auth import create_access_token

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
                        "data_base": str(tmp_path),
                        "data_dirs": [],
                    }
                },
                "users": {
                    "alice": {
                        "hashed_password": _make_hash("testpass"),
                        "accounts": ["test_org"],
                    },
                    "bob": {
                        "hashed_password": _make_hash("testpass"),
                        "accounts": ["other_org"],
                    },
                },
            }
        )
    )

    env_backup = {k: os.environ.get(k) for k in ("DONORPIPE_CONFIG", "DONORPIPE_JWT_SECRET")}
    os.environ["DONORPIPE_CONFIG"] = str(config_file)
    os.environ["DONORPIPE_JWT_SECRET"] = TEST_SECRET

    with TestClient(app) as c:
        yield c, tmp_path

    for k, v in env_backup.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def alice_headers() -> dict:
    os.environ["DONORPIPE_JWT_SECRET"] = TEST_SECRET
    token = create_access_token("alice", ["test_org"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def bob_headers() -> dict:
    os.environ["DONORPIPE_JWT_SECRET"] = TEST_SECRET
    token = create_access_token("bob", ["other_org"])
    return {"Authorization": f"Bearer {token}"}


# --- POST /accounts/{id}/refresh ---

def test_post_refresh_creates_state_file(client, alice_headers):
    c, tmp_path = client
    response = c.post("/accounts/test_org/refresh", headers=alice_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "requested"
    assert "requested_at" in data
    state_file = tmp_path / "refresh_state.json"
    assert state_file.exists()
    state = json.loads(state_file.read_text())
    assert state["requested_at"] == data["requested_at"]


def test_post_refresh_without_token_returns_401(client):
    c, _ = client
    response = c.post("/accounts/test_org/refresh")
    assert response.status_code == 401


def test_post_refresh_wrong_account_returns_403(client, bob_headers):
    # bob has other_org, not test_org
    c, _ = client
    response = c.post("/accounts/test_org/refresh", headers=bob_headers)
    assert response.status_code == 403


# --- GET /accounts/{id}/refresh ---

def test_get_status_no_request(client, alice_headers):
    c, _ = client
    response = c.get("/accounts/test_org/refresh", headers=alice_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] is False
    assert data["requested_at"] is None


def test_get_status_pending_after_post(client, alice_headers):
    c, _ = client
    c.post("/accounts/test_org/refresh", headers=alice_headers)
    response = c.get("/accounts/test_org/refresh", headers=alice_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] is True
    assert data["requested_at"] is not None


def test_get_status_satisfied_when_graph_newer(client, alice_headers):
    c, tmp_path = client
    # Post a refresh request
    c.post("/accounts/test_org/refresh", headers=alice_headers)

    # Write a graph.json with generated_at 1 minute in the future
    future_ts = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    graph = {"_meta": {"generated_at": future_ts, "files": []}}
    (tmp_path / "graph.json").write_text(json.dumps(graph))

    response = c.get("/accounts/test_org/refresh", headers=alice_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] is False
    assert data["last_updated"] == future_ts


def test_get_status_without_token_returns_401(client):
    c, _ = client
    response = c.get("/accounts/test_org/refresh")
    assert response.status_code == 401


def test_get_status_wrong_account_returns_403(client, bob_headers):
    c, _ = client
    response = c.get("/accounts/test_org/refresh", headers=bob_headers)
    assert response.status_code == 403
