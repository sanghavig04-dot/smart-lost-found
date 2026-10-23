"""Runtime settings, read from environment variables (see .env.example)."""
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "lostfound")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))

# Matching: final score = IMAGE_WEIGHT * image + (1 - IMAGE_WEIGHT) * text
IMAGE_WEIGHT = float(os.getenv("IMAGE_WEIGHT", "0.7"))
# Raw cosine similarity between unrelated MobileNetV2 embeddings is already
# fairly high, so we rescale from [IMAGE_FLOOR, 1] to [0, 1]. Tune on real data.
IMAGE_FLOOR = float(os.getenv("IMAGE_FLOOR", "0.5"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.35"))
