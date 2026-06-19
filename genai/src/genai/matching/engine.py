"""
Face matching engine — embedding models + cosine similarity.
Supports facenet, clip, and insightface.
"""
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image
from rembg import remove, new_session

from genai.core.config import DATA_DIR
from genai.core.db import get_all_embeddings, get_player

FACENET_MODEL     = "Facenet512"
CLIP_MODEL_ID     = "openai/clip-vit-large-patch14"
INSIGHTFACE_MODEL = "buffalo_l"

EMBEDDINGS_FILES = {
    "facenet":     str(DATA_DIR / "embeddings.npy"),
    "clip":        str(DATA_DIR / "embeddings_clip.npy"),
    "insightface": str(DATA_DIR / "embeddings_insightface.npy"),
}

_rembg_session   = None
_clip_model      = None
_clip_processor  = None
_insightface_app = None


# ── Preprocessing ─────────────────────────────────────────────────────────────

def preprocess_user_photo(img_path: str, bg_color=(0, 177, 64)) -> str:
    """Remove background, fill green, return path to temp file."""
    global _rembg_session
    if _rembg_session is None:
        _rembg_session = new_session("u2net_human_seg")

    pil_img = Image.open(img_path).convert("RGBA")
    result  = remove(pil_img, session=_rembg_session)
    bg      = Image.new("RGBA", result.size, (*bg_color, 255))
    bg.paste(result, mask=result.split()[3])

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    bg.convert("RGB").save(tmp.name, quality=95)
    return tmp.name


# ── Similarity ────────────────────────────────────────────────────────────────

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between vector a (D,) and matrix b (N, D). Returns (N,)."""
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


# ── Embedding: FaceNet512 ─────────────────────────────────────────────────────

def get_user_embedding_facenet(img_path: str) -> np.ndarray:
    """
    Compute a FaceNet512 embedding for a user photo.

    Falls back from retinaface to opencv detector if the first attempt fails.
    Raises if no face is detected by either backend.
    """
    from deepface import DeepFace
    try:
        result = DeepFace.represent(
            img_path=img_path, model_name=FACENET_MODEL,
            enforce_detection=True, detector_backend="retinaface", align=True,
        )
    except Exception:
        result = DeepFace.represent(
            img_path=img_path, model_name=FACENET_MODEL,
            enforce_detection=True, detector_backend="opencv", align=True,
        )
    return np.array(result[0]["embedding"], dtype=np.float32)


# ── Embedding: CLIP ───────────────────────────────────────────────────────────

def get_user_embedding_clip(img_path: str) -> np.ndarray:
    """Compute a 768-dim CLIP visual embedding for a user photo."""
    import torch
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor
        print("Loading CLIP model...")
        _clip_model     = CLIPModel.from_pretrained(CLIP_MODEL_ID)
        _clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
        _clip_model.eval()
    img    = Image.open(img_path).convert("RGB")
    inputs = _clip_processor(images=img, return_tensors="pt")
    with torch.no_grad():
        vision_out = _clip_model.vision_model(pixel_values=inputs["pixel_values"])
        emb        = _clip_model.visual_projection(vision_out.pooler_output)
    return emb[0].cpu().numpy().astype(np.float32)


# ── Embedding: InsightFace ────────────────────────────────────────────────────

def get_user_embedding_insightface(img_path: str) -> np.ndarray:
    """Compute a 512-dim ArcFace embedding for a user photo. Raises if no face is found."""
    import cv2
    global _insightface_app
    if _insightface_app is None:
        from insightface.app import FaceAnalysis
        print("Loading InsightFace model...")
        _insightface_app = FaceAnalysis(
            name=INSIGHTFACE_MODEL, providers=["CPUExecutionProvider"]
        )
        _insightface_app.prepare(ctx_id=0, det_size=(640, 640))
    img   = cv2.imread(img_path)
    faces = _insightface_app.get(img)
    if not faces:
        raise ValueError("No face detected in the image")
    return faces[0].normed_embedding.astype(np.float32)


# ── Dispatcher ────────────────────────────────────────────────────────────────

def get_user_embedding(img_path: str, model: str = "facenet") -> np.ndarray:
    """Dispatch embedding extraction to the correct model backend."""
    if model == "clip":
        return get_user_embedding_clip(img_path)
    if model == "insightface":
        return get_user_embedding_insightface(img_path)
    return get_user_embedding_facenet(img_path)


# ── Match ─────────────────────────────────────────────────────────────────────

def find_matches(user_img: str, top_k: int = 3, model: str = "facenet") -> list[dict]:
    """
    Find the top_k most similar players to a user photo using cosine similarity.

    Preprocesses the photo (background removal), embeds it with the chosen model,
    and ranks against the prebuilt embedding matrix.
    """
    emb_file = EMBEDDINGS_FILES[model]
    if not Path(emb_file).exists():
        raise FileNotFoundError(
            f"{emb_file} not found — run: python -m genai.pipeline --steps embed --models {model}"
        )

    matrix, rows = get_all_embeddings(emb_file)

    print(f"Removing background from {user_img}...")
    processed = preprocess_user_photo(user_img)
    print(f"Computing embedding with {model.upper()}...")
    user_emb  = get_user_embedding(processed, model)

    sims    = cosine_similarity(user_emb, matrix)
    top_idx = np.argsort(sims)[::-1][:top_k]

    return [
        {
            "rank":       rank,
            "id":         rows[idx]["id"],
            "name":       rows[idx]["name"],
            "team":       rows[idx]["team"],
            "face_path":  rows[idx]["face_path"],
            "similarity": float(sims[idx]),
        }
        for rank, idx in enumerate(top_idx, 1)
    ]
