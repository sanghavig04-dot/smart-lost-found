"""API tests using an in-memory Mongo and a fake embedder (no TensorFlow needed)."""
import io

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from PIL import Image

from app import main


def png_bytes(color):
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "AsyncIOMotorClient", lambda *_: AsyncMongoMockClient())
    monkeypatch.setattr(main, "load_model", lambda: None)
    # Fake embedding: red-ish images -> [1, 0], blue-ish -> [0, 1]
    monkeypatch.setattr(main, "embed_image", lambda data: [1.0, 0.0] if data[-1] % 2 else [0.0, 1.0])
    monkeypatch.setattr(main, "UPLOAD_PATH", tmp_path)
    with TestClient(main.app) as c:
        yield c


def report(client, **overrides):
    data = {"type": "lost", "title": "Red backpack", "description": "zip broken", "category": "bags",
            "location": "Library", "reporter_name": "Asha", "contact_email": "asha@example.com"}
    data.update(overrides)
    return client.post("/api/items", data=data)


def test_validation(client):
    assert report(client, type="stolen").status_code == 422
    assert report(client, contact_email="nope").status_code == 422
    bad = client.post("/api/items", data={"type": "lost", "title": "x", "reporter_name": "a", "contact_email": "a@b.co"},
                      files={"image": ("x.txt", b"hello", "text/plain")})
    assert bad.status_code == 415


def test_lost_item_matches_found_item_and_hides_email_in_list(client):
    lost = report(client).json()
    assert "manage_token" in lost
    report(client, type="found", title="Red backpack", reporter_name="Ravi", contact_email="ravi@example.com")
    report(client, type="found", title="Calculus textbook", category="stationery", location="Canteen")

    listing = client.get("/api/items").json()
    assert len(listing) == 3 and all("contact_email" not in i for i in listing)

    matches = client.get(f"/api/items/{lost['id']}/matches").json()
    assert [m["item"]["title"] for m in matches] == ["Red backpack"]
    assert matches[0]["item"]["contact_email"] == "ravi@example.com"


def test_resolve_requires_token(client):
    item = report(client).json()
    assert client.patch(f"/api/items/{item['id']}/resolve", json={"token": "wrong"}).status_code == 403
    assert client.patch(f"/api/items/{item['id']}/resolve", json={"token": item["manage_token"]}).status_code == 200
    assert client.get("/api/items").json() == []


def test_image_upload_is_stored(client):
    res = client.post("/api/items", data={"type": "found", "title": "Bottle", "reporter_name": "A", "contact_email": "a@b.co"},
                      files={"image": ("b.png", png_bytes("red"), "image/png")})
    assert res.status_code == 201 and res.json()["image_url"].startswith("/uploads/")
