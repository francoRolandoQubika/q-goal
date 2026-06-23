"""
FastAPI service — World Cup 2026 face matching + office quiz
Endpoints:
  POST /match            Upload a photo, get top-K lookalike players
  GET  /players/{id}     Get player metadata by ID
  GET  /faces/{id}       Get player face image
  POST /quiz/start       Start a new quiz session
  POST /quiz/answer      Submit an answer, get next question or final results
"""
import uuid
import tempfile
import numpy as np
from pathlib import Path
from typing import Literal, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from genai.core.config import API_PORT, DATA_DIR
from genai.core.db import get_all_embeddings, get_player
from genai.matching.engine import preprocess_user_photo, get_user_embedding, cosine_similarity, EMBEDDINGS_FILES
from genai.agent.graph import start_quiz_session, process_quiz_answers
from genai.agent.questions import NUM_QUESTIONS

PORT = API_PORT

app = FastAPI(title="WC2026 Face Match API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_matrices: dict[str, np.ndarray] = {}
_rows: list | None = None


@app.on_event("startup")
def load_db():
    """Pre-load all embedding matrices and player rows into memory at server start."""
    global _rows
    matrix, _rows = get_all_embeddings(EMBEDDINGS_FILES["facenet"])
    _matrices["facenet"] = matrix
    for model_name in ("clip", "insightface"):
        f = EMBEDDINGS_FILES[model_name]
        if Path(f).is_file():
            m, _ = get_all_embeddings(f)
            _matrices[model_name] = m
            print(f"[api]   + {model_name} loaded")
        else:
            print(f"[api]   - {model_name} not found (run: uv run genai-pipeline --steps embed --models {model_name})")
    print(f"[api] Ready — {len(_rows)} players indexed, models: {list(_matrices)}")


class PlayerMatch(BaseModel):
    id:         int
    name:       str
    team:       str
    face_path:  str
    similarity: float
    rank:       int
    position:   str | None = None
    dob:        str | None = None
    club:       str | None = None
    height_cm:  int | None = None
    caps:       int | None = None
    goals:      int | None = None


class MatchResponse(BaseModel):
    matches: list[PlayerMatch]
    model:   str


@app.post("/match", response_model=MatchResponse)
async def match_face(
    photo: UploadFile = File(...),
    top:   int = Query(default=3, ge=1, le=20),
    model: Literal["facenet", "clip", "insightface"] = Query(default="clip"),
):
    """Upload a photo and receive the top-K most similar World Cup 2026 players."""
    if model not in _matrices:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' not loaded. Run: python -m genai.pipeline --steps embed --models {model}",
        )

    suffix = Path(photo.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await photo.read())
        tmp_path = tmp.name

    try:
        processed = preprocess_user_photo(tmp_path)
        user_emb  = get_user_embedding(processed, model)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process face: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    sims    = cosine_similarity(user_emb, _matrices[model])
    top_idx = np.argsort(sims)[::-1][:top]

    matches = []
    for rank, idx in enumerate(top_idx, 1):
        row        = _rows[idx]
        player_row = get_player(row["id"])
        matches.append(PlayerMatch(
            id=row["id"], name=row["name"], team=row["team"],
            face_path=row["face_path"],
            similarity=round(float(sims[idx]), 4), rank=rank,
            position=player_row["position"]  if player_row else None,
            dob=player_row["dob"]            if player_row else None,
            club=player_row["club"]          if player_row else None,
            height_cm=player_row["height_cm"] if player_row else None,
            caps=player_row["caps"]          if player_row else None,
            goals=player_row["goals"]        if player_row else None,
        ))

    return MatchResponse(matches=matches, model=model)


@app.get("/players/{player_id}")
def get_player_info(player_id: int):
    """Return full metadata for a player by their DB primary key."""
    row = get_player(player_id)
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    return {
        "id": row["id"], "name": row["name"], "team": row["team"],
        "face_path": row["face_path"], "position": row["position"],
        "dob": row["dob"], "club": row["club"], "height_cm": row["height_cm"],
        "caps": row["caps"], "goals": row["goals"],
    }


@app.get("/faces/{player_id}")
def get_face_image(player_id: int):
    """Serve the cropped face JPEG for a player by their DB primary key."""
    row = get_player(player_id)
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    face_path = Path(row["face_path"])
    if not face_path.is_absolute():
        face_path = DATA_DIR / face_path
    if not face_path.exists():
        raise HTTPException(status_code=404, detail="Face image not found on disk")
    return FileResponse(face_path, media_type="image/jpeg")


@app.get("/photos/{player_id}")
def get_player_photo(player_id: int):
    """Serve the original full headshot (from players/) by their DB primary key."""
    row = get_player(player_id)
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    face_path = Path(row["face_path"])
    photo_dir = DATA_DIR / "players" / face_path.parent.name
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = photo_dir / (face_path.stem + ext)
        if candidate.exists():
            return FileResponse(candidate, media_type=f"image/{ext.lstrip('.')}")
    raise HTTPException(status_code=404, detail="Player photo not found on disk")


# ── Quiz endpoints ─────────────────────────────────────────────────────────────

class QuizStartRequest(BaseModel):
    role: str

class QuizAnswerOption(BaseModel):
    key:  str
    text: str

class QuizQuestion(BaseModel):
    question: str
    answers:  list[QuizAnswerOption]

class QuizStartResponse(BaseModel):
    session_id:      str
    questions:       list[QuizQuestion]
    total_questions: int


class QuizAnswerRequest(BaseModel):
    session_id: str
    answers:    list[str]


class QuizPlayer(BaseModel):
    id:        int
    name:      str
    team:      str
    face_path: str
    position:  str | None = None
    dob:       str | None = None
    club:      str | None = None
    height_cm: int | None = None
    caps:      int | None = None
    goals:     int | None = None


class QuizAssignment(BaseModel):
    title:       str
    description: str
    player:      QuizPlayer | None


class QuizComplete(BaseModel):
    status:      Literal["complete"]
    session_id:  str
    assignments: list[QuizAssignment]
    outro:       str


@app.post("/quiz/start", response_model=QuizStartResponse)
async def quiz_start(body: QuizStartRequest):
    """Generate all 4 questions tailored to the user's role at Qubika. Save session_id and send all answers in one call."""
    try:
        result = start_quiz_session(role=body.role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return QuizStartResponse(
        session_id=result["session_id"],
        questions=result["questions"],
        total_questions=NUM_QUESTIONS,
    )


@app.post("/quiz/answer", response_model=QuizComplete)
async def quiz_answer(body: QuizAnswerRequest):
    """
    Submit all answers at once and receive the final team assignments.
    Body: { "session_id": "...", "answers": ["A", "B", "C", "D"] }
    """
    if len(body.answers) != NUM_QUESTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Expected {NUM_QUESTIONS} answers, got {len(body.answers)}.",
        )
    try:
        result = process_quiz_answers(body.session_id, body.answers)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    assignments = [
        QuizAssignment(
            title=a["title"],
            description=a["description"],
            player=QuizPlayer(
                id=a["player"]["id"],
                name=a["player"]["name"],
                team=a["player"]["team"].replace("_", " ").title(),
                face_path=a["player"]["face_path"],
                position=a["player"].get("position"),
                dob=a["player"].get("dob"),
                club=a["player"].get("club"),
                height_cm=a["player"].get("height_cm"),
                caps=a["player"].get("caps"),
                goals=a["player"].get("goals"),
            ) if a["player"] else None,
        )
        for a in result["assignments"]
    ]
    return QuizComplete(
        status="complete",
        session_id=body.session_id,
        assignments=assignments,
        outro=result["outro"],
    )


def serve():
    """Entry point for `uv run genai-api` or direct invocation."""
    import uvicorn
    uvicorn.run("genai.api:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    serve()
