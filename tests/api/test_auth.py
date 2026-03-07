"""Auth integration tests."""

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
                        "accounts": ["test_org"],
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


def _token_for(accounts: list[str]) -> str:
    os.environ["DONORPIPE_JWT_SECRET"] = TEST_SECRET
    return create_access_token("alice", accounts)


def test_login_valid_credentials(client):
    res = client.post("/token", data={"username": "alice", "password": "testpass"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    res = client.post("/token", data={"username": "alice", "password": "wrong"})
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post("/token", data={"username": "nobody", "password": "testpass"})
    assert res.status_code == 401


def test_graph_no_token(client):
    res = client.get("/accounts/test_org/graph")
    assert res.status_code == 401


def test_graph_wrong_account(client):
    # Alice only has test_org; requesting other_org → 403
    token = _token_for(["test_org"])
    res = client.get(
        "/accounts/other_org/graph",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_graph_valid_token(client):
    token = _token_for(["test_org"])
    res = client.get(
        "/accounts/test_org/graph",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
