"""
Generates facial embeddings for all cropped faces in faces/ and saves them to:
  facenet  →  embeddings.npy        (N×512 float32)  +  metadata.json
  clip     →  embeddings_clip.npy   (N×768 float32)  +  metadata.json (shared)
  insightface → embeddings_insightface.npy  (N×512 float32)

Run once after crop.py. Use --model to choose the encoder.
"""
import argparse
import json
import numpy as np
from pathlib import Path

from genai.core.config import DATA_DIR

FACES_DIR     = DATA_DIR / "faces"
METADATA_FILE = DATA_DIR / "metadata.json"

FACENET_MODEL     = "Facenet512"
CLIP_MODEL_ID     = "openai/clip-vit-large-patch14"
INSIGHTFACE_MODEL = "buffalo_l"

EMBEDDINGS_FILES = {
    "facenet":     str(DATA_DIR / "embeddings.npy"),
    "clip":        str(DATA_DIR / "embeddings_clip.npy"),
    "insightface": str(DATA_DIR / "embeddings_insightface.npy"),
}

_clip_model      = None
_clip_processor  = None
_insightface_app = None


def get_embedding_facenet(img_path: str) -> np.ndarray | None:
    """Return a 512-dim FaceNet embedding for img_path, or None if extraction fails."""
    from deepface import DeepFace
    try:
        result = DeepFace.represent(
            img_path=img_path,
            model_name=FACENET_MODEL,
            enforce_detection=False,
            detector_backend="retinaface",
            align=True,
        )
        return np.array(result[0]["embedding"], dtype=np.float32)
    except Exception as e:
        print(f"    [skip] {img_path}: {e}")
        return None


def _load_insightface():
    global _insightface_app
    if _insightface_app is None:
        from insightface.app import FaceAnalysis
        print(f"Loading InsightFace model {INSIGHTFACE_MODEL} ...")
        _insightface_app = FaceAnalysis(
            name=INSIGHTFACE_MODEL,
            providers=["CPUExecutionProvider"],
        )
        _insightface_app.prepare(ctx_id=0, det_size=(640, 640))
    return _insightface_app


def get_embedding_insightface(img_path: str) -> np.ndarray | None:
    """Return a 512-dim L2-normalised ArcFace embedding, or None if no face is found."""
    import cv2
    try:
        app   = _load_insightface()
        img   = cv2.imread(img_path)
        faces = app.get(img)
        if not faces:
            print(f"    [skip] {img_path}: no face detected")
            return None
        return faces[0].normed_embedding.astype(np.float32)
    except Exception as e:
        print(f"    [skip] {img_path}: {e}")
        return None


def _load_clip():
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor
        print(f"Loading CLIP model {CLIP_MODEL_ID} ...")
        _clip_model     = CLIPModel.from_pretrained(CLIP_MODEL_ID)
        _clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
        _clip_model.eval()
    return _clip_model, _clip_processor


def get_embedding_clip(img_path: str) -> np.ndarray | None:
    """Return a 768-dim CLIP visual embedding for img_path, or None on error."""
    import torch
    from PIL import Image
    try:
        model, processor = _load_clip()
        img    = Image.open(img_path).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            vision_out = model.vision_model(pixel_values=inputs["pixel_values"])
            emb        = model.visual_projection(vision_out.pooler_output)
        return emb[0].cpu().numpy().astype(np.float32)
    except Exception as e:
        print(f"    [skip] {img_path}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Build face embedding matrix")
    parser.add_argument(
        "--model", choices=["facenet", "clip", "insightface"], default="facenet",
        help="Embedding model to use (default: facenet)",
    )
    args = parser.parse_args()

    if not FACES_DIR.exists():
        print(f"No faces/ directory at {FACES_DIR}. Run crop step first.")
        return

    get_embedding = {
        "facenet":     get_embedding_facenet,
        "clip":        get_embedding_clip,
        "insightface": get_embedding_insightface,
    }[args.model]
    out_file = EMBEDDINGS_FILES[args.model]

    face_files = sorted(p for p in FACES_DIR.rglob("*.jpg") if p.is_file())
    total = len(face_files)
    print(f"Processing {total} faces with {args.model.upper()} → {out_file}\n")

    embeddings = []
    metadata   = []
    ok = fail  = 0

    for i, face_path in enumerate(face_files, 1):
        team = face_path.parent.name
        name = face_path.stem.replace("_", " ").title()
        print(f"[{i}/{total}] {team} / {name}", end=" ... ", flush=True)

        emb = get_embedding(str(face_path))
        if emb is not None:
            embeddings.append(emb)
            metadata.append({
                "idx":       len(embeddings) - 1,
                "name":      name,
                "team":      team,
                "face_path": str(face_path.relative_to(DATA_DIR)),
            })
            print("✓")
            ok += 1
        else:
            print("✗")
            fail += 1

    if not embeddings:
        print("No embeddings generated.")
        return

    matrix = np.stack(embeddings)
    np.save(out_file, matrix)

    # metadata.json is shared across models (same face ordering).
    # Only overwrite when running facenet (canonical pass) or when it doesn't exist yet.
    if args.model == "facenet" or not METADATA_FILE.exists():
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"Metadata → {METADATA_FILE}")

    print(f"\nSaved {ok} embeddings → {out_file} {matrix.shape}")
    if fail:
        print(f"Skipped: {fail}")


if __name__ == "__main__":
    main()
