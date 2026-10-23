import asyncio
import io
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image
from pydantic import BaseModel

from . import config
from .embedding import embed_image, load_model
from .matching import rank_matches

CATEGORIES = {"electronics", "bags", "documents", "keys", "clothing", "stationery", "other"}
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

UPLOAD_PATH = Path(config.UPLOAD_DIR)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = AsyncIOMotorClient(config.MONGO_URL)
    app.state.db = app.state.client[config.DB_NAME]
    await app.state.db.items.create_index([("type", 1), ("status", 1), ("created_at", -1)])
    await asyncio.to_thread(load_model)  # warm up so the first upload isn't slow
    yield
    app.state.client.close()


app = FastAPI(title="Smart Lost & Found", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_PATH), name="uploads")


def public(doc: dict, with_contact: bool = False) -> dict:
    out = {
        "id": str(doc["_id"]),
        "type": doc["type"],
        "title": doc["title"],
        "description": doc["description"],
        "category": doc["category"],
        "location": doc["location"],
        "reporter_name": doc["reporter_name"],
        "image_url": doc.get("image_url"),
        "status": doc["status"],
        "created_at": doc["created_at"].isoformat(),
    }
    if with_contact:
        out["contact_email"] = doc["contact_email"]
    return out


def to_object_id(item_id: str) -> ObjectId:
    try:
        return ObjectId(item_id)
    except (InvalidId, TypeError):
        raise HTTPException(404, "Item not found")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/items", status_code=201)
async def create_item(
    type: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form("other"),
    location: str = Form(""),
    reporter_name: str = Form(...),
    contact_email: str = Form(...),
    image: UploadFile | None = File(None),
):
    if type not in {"lost", "found"}:
        raise HTTPException(422, "type must be 'lost' or 'found'")
    if not title.strip() or not reporter_name.strip():
        raise HTTPException(422, "Title and your name are required")
    if not EMAIL_RE.match(contact_email.strip()):
        raise HTTPException(422, "Enter a valid email address")
    if category not in CATEGORIES:
        category = "other"

    image_url, embedding = None, None
    if image is not None and image.filename:
        ext = IMAGE_TYPES.get(image.content_type)
        if ext is None:
            raise HTTPException(415, "Upload a JPG, PNG or WebP image")
        data = await image.read()
        if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"Image must be under {config.MAX_UPLOAD_MB} MB")
        try:
            Image.open(io.BytesIO(data)).verify()
        except Exception:
            raise HTTPException(400, "That file isn't a readable image")
        filename = f"{uuid.uuid4().hex}.{ext}"
        (UPLOAD_PATH / filename).write_bytes(data)
        image_url = f"/uploads/{filename}"
        embedding = await asyncio.to_thread(embed_image, data)

    token = secrets.token_urlsafe(16)
    doc = {
        "type": type,
        "title": title.strip(),
        "description": description.strip(),
        "category": category,
        "location": location.strip(),
        "reporter_name": reporter_name.strip(),
        "contact_email": contact_email.strip(),
        "image_url": image_url,
        "embedding": embedding,
        "status": "open",
        "manage_token": token,
        "created_at": datetime.now(timezone.utc),
    }
    result = await app.state.db.items.insert_one(doc)
    doc["_id"] = result.inserted_id
    # The token is returned once, to the reporter only. It's needed to mark the item resolved.
    return {**public(doc), "manage_token": token}


@app.get("/api/items")
async def list_items(
    type: str | None = Query(None, pattern="^(lost|found)$"),
    q: str | None = None,
    limit: int = Query(60, ge=1, le=200),
):
    query: dict = {"status": "open"}
    if type:
        query["type"] = type
    if q and q.strip():
        rx = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"title": rx}, {"description": rx}, {"location": rx}]
    cursor = app.state.db.items.find(query).sort("created_at", -1).limit(limit)
    return [public(d) async for d in cursor]


@app.get("/api/items/{item_id}/matches")
async def get_matches(item_id: str):
    items = app.state.db.items
    item = await items.find_one({"_id": to_object_id(item_id)})
    if not item:
        raise HTTPException(404, "Item not found")
    opposite = "found" if item["type"] == "lost" else "lost"
    candidates = [d async for d in items.find({"type": opposite, "status": "open"})]
    ranked = rank_matches(item, candidates)
    return [{"score": round(s, 3), "item": public(c, with_contact=True)} for s, c in ranked]


class ResolveBody(BaseModel):
    token: str


@app.patch("/api/items/{item_id}/resolve")
async def resolve_item(item_id: str, body: ResolveBody):
    items = app.state.db.items
    item = await items.find_one({"_id": to_object_id(item_id)})
    if not item:
        raise HTTPException(404, "Item not found")
    if not secrets.compare_digest(item["manage_token"], body.token):
        raise HTTPException(403, "Only the person who reported this item can close it")
    await items.update_one({"_id": item["_id"]}, {"$set": {"status": "resolved"}})
    return {"id": item_id, "status": "resolved"}
