"""Image -> feature vector using MobileNetV2 (ImageNet weights, no classifier head).

TensorFlow is imported lazily so the rest of the app (and the unit tests)
can run without it installed.
"""
import io

import numpy as np
from PIL import Image

_model = None


def load_model():
    """Load the model once; call at startup to avoid a slow first request."""
    global _model
    if _model is None:
        from tensorflow.keras.applications import MobileNetV2

        _model = MobileNetV2(
            weights="imagenet",
            include_top=False,
            pooling="avg",
            input_shape=(224, 224, 3),
        )
    return _model


def embed_image(data: bytes) -> list[float]:
    """Return an L2-normalised 1280-d embedding for the image bytes."""
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

    img = Image.open(io.BytesIO(data)).convert("RGB").resize((224, 224))
    batch = preprocess_input(np.asarray(img, dtype="float32")[None, ...])
    vec = load_model().predict(batch, verbose=0)[0]
    norm = np.linalg.norm(vec)
    if norm:
        vec = vec / norm
    return vec.astype("float32").tolist()
