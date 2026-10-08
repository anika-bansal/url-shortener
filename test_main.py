import os
os.environ["DB_NAME"] = "test.db"

import pytest
from fastapi.testclient import TestClient
from database import init_db, get_connection
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM urls")
    conn.commit()
    conn.close()
    yield

def test_shorten_valid_url():
    response = client.post("/shorten", json={"url": "https://www.example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data

def test_shorten_invalid_url():
    response = client.post("/shorten", json={"url": "banana"})
    assert response.status_code == 422

def test_redirect_to_existing_code():
    shorten_response = client.post("/shorten", json={"url": "https://www.example.com"})
    short_code = shorten_response.json()["short_code"]
    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 302
    assert redirect_response.headers["location"] == "https://www.example.com/"

def test_redirect_unknown_code():
    response = client.get("/doesnotexist123")
    assert response.status_code == 404

def test_short_url_uses_request_host():
    response = client.post("/shorten", json={"url": "https://www.python.org"})
    data = response.json()
    assert "127.0.0.1" not in data["short_url"]
    assert data["short_url"].endswith(data["short_code"])
