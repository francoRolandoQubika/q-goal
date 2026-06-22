"""
Quiz controller — simplified, no LangGraph.

New flow (2 HTTP calls total):
  POST /quiz/start  → generates all 4 questions at once (1 LLM call)
  POST /quiz/answer → receives all 4 answers, extracts traits, assigns players,
                      generates per-player descriptions + outro (2 LLM calls)

Total: 3 LLM calls per session (down from 14 with the interrupt pattern).
Sessions are kept in-memory — reset on server restart.
"""
import json
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from genai.agent.questions import (
    QUESTION_THEMES,
    NUM_QUESTIONS,
    OUTPUT_SLOTS,
    find_all_slot_players,
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9)

SYSTEM_PROMPT = """Sos el animador de "Tu equipo del Mundial en la oficina" —
un juego que asigna jugadores del Mundial 2026 a situaciones de laburo en una software factory.
Hablás en español rioplatense (vos, che, dale) con humor tech y futbolero.
Sos conciso, directo y gracioso."""

_sessions: dict[str, dict] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json(content: str) -> object:
    """Strip markdown fences and parse JSON from an LLM response."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


# ── Session: start ────────────────────────────────────────────────────────────

def start_quiz_session() -> dict:
    """
    Generate all questions at once (1 LLM call) and store the session.
    Returns { session_id, questions: [str, ...] }.
    """
    themes_text = "\n".join(
        f'{i + 1}. Tema: {t["topic"]} — {t["hint"]}'
        for i, t in enumerate(QUESTION_THEMES)
    )

    resp = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Generá exactamente {NUM_QUESTIONS} preguntas de situaciones de oficina "
            "para una software factory argentina.\n\n"
            f"Temas en orden:\n{themes_text}\n\n"
            "Requisitos por pregunta:\n"
            "- Situación concreta y divertida con contexto tech\n"
            "- 4 opciones (A, B, C, D) que reflejen personalidades distintas\n"
            "- Usá emojis\n\n"
            'Devolvé SOLO un JSON array: [{"number": 1, "text": "..."}, ...]'
        )),
    ])

    try:
        questions_data = _parse_json(resp.content)
        questions = [q["text"] for q in questions_data]
    except Exception:
        # Fallback: split by numbered lines if JSON fails
        questions = [resp.content]

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"questions": questions}
    return {"session_id": session_id, "questions": questions}


# ── Session: process answers ──────────────────────────────────────────────────

def process_quiz_answers(session_id: str, answers: list[str]) -> dict:
    """
    Process all answers at once (2 LLM calls) and return the final team.

    Returns {
        assignments: [{ title, description, player }],
        outro: str,
    }
    """
    if session_id not in _sessions:
        raise ValueError(f"Session '{session_id}' not found or expired.")

    questions = _sessions[session_id]["questions"]

    # ── LLM call 1: extract all traits from all answers ───────────────────────
    qa_text = "\n".join(
        f"Pregunta {i + 1}: {q}\nRespuesta: {a}"
        for i, (q, a) in enumerate(zip(questions, answers))
    )

    traits_resp = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Analizá estas {NUM_QUESTIONS} respuestas y extraé un rasgo de personalidad "
            "en 3-5 palabras en inglés para cada una.\n\n"
            f"{qa_text}\n\n"
            'Devolvé SOLO un JSON array: ["trait 1", "trait 2", "trait 3", "trait 4"]'
        )),
    ])

    try:
        traits_list = _parse_json(traits_resp.content)
        traits = {f"q{i}": t for i, t in enumerate(traits_list)}
    except Exception:
        traits = {f"q{i}": "unknown" for i in range(NUM_QUESTIONS)}

    # ── Find one player per slot ──────────────────────────────────────────────
    raw_assignments = find_all_slot_players(OUTPUT_SLOTS, traits)

    # ── LLM call 2: descriptions per player + outro ───────────────────────────
    personality_summary = ", ".join(traits.values())

    slots_text = "\n".join(
        f'- {a["slot"]["title"]}: {a["player"]["name"] if a["player"] else "N/A"}'
        f' ({a["player"].get("position","?")}, {a["player"].get("caps","?")} caps)'
        if a["player"] else f'- {a["slot"]["title"]}: N/A'
        for a in raw_assignments
    )

    desc_resp = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Perfil del usuario: {personality_summary}\n\n"
            f"Equipo asignado:\n{slots_text}\n\n"
            f"Hacé dos cosas:\n"
            f"1. Para cada uno de los {len(raw_assignments)} jugadores escribí 1-2 oraciones "
            "explicando con humor tech/futbolero por qué ese jugador encaja en ese rol de oficina.\n"
            "2. Escribí un outro general (máx 4 líneas) que cruce el perfil del usuario con el equipo.\n\n"
            "Devolvé SOLO un JSON con este formato exacto:\n"
            '{"descriptions": ["desc slot 1", "desc slot 2", ...], "outro": "..."}'
        )),
    ])

    try:
        desc_data = _parse_json(desc_resp.content)
        descriptions = desc_data.get("descriptions", [""] * len(raw_assignments))
        outro = desc_data.get("outro", "")
    except Exception:
        descriptions = [""] * len(raw_assignments)
        outro = desc_resp.content

    # ── Assemble final response ───────────────────────────────────────────────
    assignments = [
        {
            "title":       a["slot"]["title"],
            "description": descriptions[i] if i < len(descriptions) else "",
            "player":      a["player"],
        }
        for i, a in enumerate(raw_assignments)
    ]

    del _sessions[session_id]

    return {"assignments": assignments, "outro": outro}
