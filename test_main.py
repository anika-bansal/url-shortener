import os
import sqlite3
os.environ["DB_NAME"] = "test.db"

import pytest
from fastapi.testclient import TestClient
from database import init_db, get_connection, get_original_url
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

def test_generate_unique_short_code_retries_on_select_collision():
    import shortener
    calls = {"count": 0}
    original_generate = shortener.generate_short_code

    def fake_generate(length=6):
        calls["count"] += 1
        if calls["count"] == 1:
            return "forced01"
        return original_generate(length)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO urls (short_code, original_url, created_at) VALUES (?, ?, ?)",
        ("forced01", "https://taken.com", "2026-01-01")
    )
    conn.commit()
    conn.close()

    shortener.generate_short_code = fake_generate
    try:
        code = shortener.generate_unique_short_code()
        assert code != "forced01"
        assert calls["count"] == 2
    finally:
        shortener.generate_short_code = original_generate


def test_create_url_with_retry_handles_insert_collision():
    import shortener
    calls = {"count": 0}
    original_create_url = shortener.create_url

    def fake_create_url(short_code, original_url):
        calls["count"] += 1
        if calls["count"] == 1:
            raise sqlite3.IntegrityError("UNIQUE constraint failed: urls.short_code")
        return original_create_url(short_code, original_url)

    shortener.create_url = fake_create_url
    try:
        code = shortener.create_url_with_retry("https://www.race-test.com")
        assert calls["count"] == 2
        assert get_original_url(code) == "https://www.race-test.com"
    finally:
        shortener.create_url = original_create_url
