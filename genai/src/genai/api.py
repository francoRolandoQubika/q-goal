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
from genai.agent.graph import start_session, submit_answer, is_complete
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
        if Path(f).exists():
            m, _ = get_all_embeddings(f)
            _matrices[model_name] = m
            print(f"[api]   + {model_name} loaded")
        else:
            print(f"[api]   - {model_name} not found (run: python -m genai.pipeline --steps embed --models {model_name})")
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
    # face_path is stored relative to DATA_DIR in the DB
    face_path = Path(row["face_path"])
    if not face_path.is_absolute():
        face_path = DATA_DIR / face_path
    if not face_path.exists():
        raise HTTPException(status_code=404, detail="Face image not found on disk")
    return FileResponse(face_path, media_type="image/jpeg")


# ── Quiz endpoints ─────────────────────────────────────────────────────────────

class QuizQuestion(BaseModel):
    status:          Literal["question"]
    session_id:      str
    question:        str
    question_number: int
    total_questions: int


class QuizPlayer(BaseModel):
    name:      str
    team:      str
    position:  str | None = None
    club:      str | None = None
    caps:      int | None = None
    goals:     int | None = None
    height_cm: int | None = None


class QuizAssignment(BaseModel):
    title:  str
    player: QuizPlayer | None


class QuizComplete(BaseModel):
    status:      Literal["complete"]
    session_id:  str
    assignments: list[QuizAssignment]
    outro:       str


def _state_to_question(session_id: str, state: dict) -> QuizQuestion:
    from langchain_core.messages import AIMessage as AI
    msgs = state.get("messages", [])
    question_text = state.get("current_question", "")
    for msg in reversed(msgs):
        if isinstance(msg, AI):
            question_text = msg.content
            break
    return QuizQuestion(
        status="question",
        session_id=session_id,
        question=question_text,
        question_number=state.get("q_index", 0),
        total_questions=NUM_QUESTIONS,
    )


def _state_to_complete(session_id: str, state: dict) -> QuizComplete:
    from langchain_core.messages import AIMessage as AI
    msgs  = state.get("messages", [])
    outro = next((m.content for m in reversed(msgs) if isinstance(m, AI)), "")

    raw = state.get("assignments") or []
    assignments = [
        QuizAssignment(
            title=a["title"],
            player=QuizPlayer(
                name=a["player"]["name"],
                team=a["player"]["team"].replace("_", " ").title(),
                position=a["player"].get("position"),
                club=a["player"].get("club"),
                caps=a["player"].get("caps"),
                goals=a["player"].get("goals"),
                height_cm=a["player"].get("height_cm"),
            ) if a["player"] else None,
        )
        for a in raw
    ]
    return QuizComplete(
        status="complete",
        session_id=session_id,
        assignments=assignments,
        outro=outro,
    )


@app.post("/quiz/start", response_model=QuizQuestion)
async def quiz_start():
    """Start a new quiz session. Returns the first dynamically generated question."""
    session_id = str(uuid.uuid4())
    try:
        state = start_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return _state_to_question(session_id, state)


@app.post("/quiz/answer", response_model=QuizQuestion | QuizComplete)
async def quiz_answer(body: dict):
    """
    Submit an answer to the current question.
    Body: { "session_id": "...", "answer": "..." }
    Returns the next question or the final team assignments when done.
    """
    session_id: str = body.get("session_id", "")
    answer:     str = body.get("answer", "")
    if not session_id or not answer:
        raise HTTPException(status_code=422, detail="session_id and answer are required")
    try:
        state = submit_answer(session_id, answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if is_complete(state):
        return _state_to_complete(session_id, state)
    return _state_to_question(session_id, state)


def serve():
    """Entry point for `uv run genai-api` or direct invocation."""
    import uvicorn
    uvicorn.run("genai.api:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    serve()
