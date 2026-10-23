# Smart Lost & Found

A campus lost-and-found web app that **matches lost items with found items automatically**.
Report an item with a photo and a few details; the app compares it against everything reported
on the other side and shows the most likely matches, ranked by score.

**Stack:** FastAPI · MongoDB · React + Vite · TensorFlow (MobileNetV2)

## How matching works

1. When a photo is uploaded, MobileNetV2 (ImageNet weights, no classifier head) turns it into a
   1280-dimensional embedding, stored in MongoDB with the item.
2. To find matches for an item, the backend loads open items of the opposite type
   (lost <-> found) and scores each one:
   - **Image score:** cosine similarity of the embeddings, rescaled from `[IMAGE_FLOOR, 1]` to `[0, 1]`.
   - **Text score:** keyword overlap across title, description and location, plus a category bonus.
   - **Final score:** `0.7 * image + 0.3 * text` (weights configurable). If either item has no photo,
     the text score is used alone.
3. Results above `MATCH_THRESHOLD` are returned best-first.

The scoring code is in [`backend/app/matching.py`](backend/app/matching.py) and is pure Python
with unit tests, so you can tune it without loading TensorFlow.

## Features

- Report lost or found items with photo, category and location
- Ranked match suggestions, shown straight after reporting
- Search and filter the open items
- Contact details are hidden from the public list and only shown on match results
- Reporters get a private token (stored in their browser) that lets only them mark an item as returned
- Image type, size and content validation

## Run it

**Option A: Docker for the backend, npm for the frontend**

```bash
docker compose up --build        # MongoDB + API on http://localhost:8000
cd frontend
npm install
npm run dev                      # UI on http://localhost:5173
```

The first start downloads the MobileNetV2 weights (about 14 MB) and caches them in a Docker volume.

**Option B: everything local**

```bash
# MongoDB must be running on localhost:27017
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

cd ../frontend
npm install && npm run dev
```

Interactive API docs: http://localhost:8000/docs

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/items` | Report an item (multipart form, optional `image`). Returns a one-time `manage_token`. |
| `GET` | `/api/items?type=&q=` | List open items; filter by `lost`/`found` and search text. |
| `GET` | `/api/items/{id}/matches` | Ranked possible matches, with contact email. |
| `PATCH` | `/api/items/{id}/resolve` | Mark as returned (requires `{ "token": ... }`). |
| `GET` | `/api/health` | Health check. |

## Tests

```bash
cd backend
pytest
```

Covers the scoring logic and the API (validation, matching, privacy, resolve tokens) using an
in-memory MongoDB and a fake embedder.

## Project structure

```
backend/
  app/
    main.py        # routes, validation, storage
    matching.py    # scoring (pure functions)
    embedding.py   # MobileNetV2 feature extraction
    config.py      # environment settings
  tests/
frontend/
  src/
    App.jsx        # feed, filters, state
    components/    # ItemTag, ReportDialog, MatchesDialog
docker-compose.yml
```

## Limitations and next steps

- Matching runs against all open items of the opposite type, which is fine for one campus but would
  need a vector index (for example MongoDB Atlas Vector Search or FAISS) at larger scale.
- `IMAGE_FLOOR` and `MATCH_THRESHOLD` are starting values. Tune them on real photos from your campus.
- No user accounts yet. Ownership uses a per-browser token. Adding login (for example college email
  OTP) would let people manage items across devices.
- Email notifications when a new item matches an existing report.

## License

MIT
