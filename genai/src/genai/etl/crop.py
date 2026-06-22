"""
Face cropper — detects and crops player faces from raw headshots.
Reads from {DATA_DIR}/players/, removes background, crops to 300x300, writes to {DATA_DIR}/faces/.
"""
import io
import cv2
import json
import numpy as np
from pathlib import Path
from PIL import Image
from rembg import remove, new_session
from deepface import DeepFace

from genai.core.config import DATA_DIR

INPUT_DIR = DATA_DIR / "players"
OUTPUT_DIR = DATA_DIR / "faces"
FACE_SIZE = (300, 300)
MARGIN = 0.4

_rembg_session = None


def remove_background(img_path: Path, bg_color=(0, 177, 64)) -> np.ndarray:
    """Remove background and fill with bg_color (BGR). Returns cv2 image."""
    global _rembg_session
    if _rembg_session is None:
        _rembg_session = new_session("u2net_human_seg")

    pil_img = Image.open(img_path).convert("RGBA")
    result = remove(pil_img, session=_rembg_session)

    background = Image.new("RGBA", result.size, (*bg_color[::-1], 255))
    background.paste(result, mask=result.split()[3])
    composite = background.convert("RGB")

    return cv2.cvtColor(np.array(composite), cv2.COLOR_RGB2BGR)


def crop_face(img_path: Path, out_path: Path, margin: float = MARGIN) -> bool:
    """Detect the face in img_path, remove background, and save a square crop to out_path."""
    try:
        faces = DeepFace.extract_faces(
            img_path=str(img_path),
            detector_backend="retinaface",
            enforce_detection=True,
            align=True,
        )
    except Exception:
        try:
            faces = DeepFace.extract_faces(
                img_path=str(img_path),
                detector_backend="opencv",
                enforce_detection=True,
                align=True,
            )
        except Exception as e:
            print(f"    [no face] {img_path.name}: {e}")
            return False

    if not faces:
        return False

    img = remove_background(img_path)
    if img is None:
        return False

    region = faces[0]["facial_area"]
    x, y, w, h = region["x"], region["y"], region["w"], region["h"]

    side = max(w, h)
    mx = int(side * margin)
    cx, cy = x + w // 2, y + h // 2

    x1 = max(0, cx - side // 2 - mx)
    y1 = max(0, cy - side // 2 - mx)
    x2 = min(img.shape[1], cx + side // 2 + mx)
    y2 = min(img.shape[0], cy + side // 2 + mx)

    crop = img[y1:y2, x1:x2]
    crop = cv2.resize(crop, FACE_SIZE)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return True


def main():
    if not INPUT_DIR.exists():
        print("No players/ directory found. Run scraper first.")
        return

    ok = 0
    fail = 0
    updated_manifest = []

    for team_dir in sorted(INPUT_DIR.iterdir()):
        if not team_dir.is_dir():
            continue
        print(f"\n{team_dir.name}")
        for photo in sorted(team_dir.iterdir()):
            if photo.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            out_path = (OUTPUT_DIR / team_dir.name / photo.stem).with_suffix(".jpg")

            if out_path.exists():
                print(f"  ~ {photo.stem} (already exists)")
                ok += 1
                updated_manifest.append({
                    "team": team_dir.name,
                    "name": photo.stem,
                    "original": str(photo),
                    "face": str(out_path),
                })
                continue

            if crop_face(photo, out_path):
                print(f"  ✓ {photo.stem}")
                ok += 1
                updated_manifest.append({
                    "team": team_dir.name,
                    "name": photo.stem,
                    "original": str(photo),
                    "face": str(out_path),
                })
            else:
                print(f"  ✗ {photo.stem}")
                fail += 1

    with open(DATA_DIR / "faces_manifest.json", "w") as f:
        json.dump(updated_manifest, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Cropped: {ok} | Failed: {fail}")
    print(f"Faces saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
