"""
Office-themed quiz questions + multi-player DB matching.

Each answer builds a personality profile, then we assign one player per
"workplace relationship" category (birra, sprint, deploy en viernes, etc.)
"""
import sqlite3
from pathlib import Path
from typing import Any

from genai.core.config import DATA_DIR

DB_FILE = str(DATA_DIR / "players.db")

# ── Teams included in the quiz pool ──────────────────────────────────────────
QUIZ_TEAMS = {
    # Latin America
    "argentina", "brazil", "uruguay", "colombia",
    "mexico", "ecuador", "paraguay",
    # Europe — superstar nations
    "spain", "france", "england", "portugal",
    "germany", "netherlands", "norway", "belgium",
    "croatia",
    # Rest of world — iconic players
    "korea_republic", "egypt", "morocco", "senegal", "japan", "usa",
}

# ── Question themes (LLM generates the actual question text each run) ─────────

QUESTION_THEMES = [
    {
        "topic": "manejo de crisis técnicas",
        "hint":  "situaciones de bugs en producción, incidentes, sistemas caídos en el peor momento",
    },
    {
        "topic": "dinámica de equipo y comunicación",
        "hint":  "standups, reuniones, Slack, cómo se relaciona con el equipo y el PM",
    },
    {
        "topic": "calidad del código y reviews",
        "hint":  "pull requests, tests, deuda técnica, documentación, refactors",
    },
    {
        "topic": "presión, deadlines y sprint",
        "hint":  "cómo gestiona el tiempo, los deploys, el scope y la presión del sprint",
    },
]

NUM_QUESTIONS = len(QUESTION_THEMES)

# ── Output slot definitions ───────────────────────────────────────────────────

OUTPUT_SLOTS = [
    {
        "title":   "El jugador con el que tomarías una birra 🍺",
        "key":     "birra",
        "persona": "fun, charismatic, outgoing — MF or FW, lots of caps (experience = good stories)",
        "filters": {"position_in": ["MF", "FW"], "caps_range": (40, 999)},
    },
    {
        "title":   "El jugador con el que resolverías tu peor sprint 💻",
        "key":     "sprint",
        "persona": "reliable, hardworking, experienced — DF or MF, high caps",
        "filters": {"position_in": ["DF", "MF"], "caps_range": (50, 999)},
    },
    {
        "title":   "El jugador que deployaría en viernes 🔥",
        "key":     "deploy",
        "persona": "bold, impulsive, low experience — FW, low caps (rookie energy)",
        "filters": {"position_in": ["FW"], "caps_range": (0, 25)},
    },
    {
        "title":   "El jugador que haría el standup más largo 🎙️",
        "key":     "standup",
        "persona": "talkative, expressive — any position, very high caps (veteran who has opinions)",
        "filters": {"position_in": ["MF", "FW"], "caps_range": (80, 999)},
    },
    {
        "title":   "El jugador que nunca escribe tests 😅",
        "key":     "tests",
        "persona": "creative but careless — FW, moderate caps",
        "filters": {"position_in": ["FW"], "caps_range": (10, 60), "goals_range": (5, 999)},
    },
    {
        "title":   "El jugador con el que harías pair programming 🧑‍💻",
        "key":     "pair",
        "persona": "methodical, precise, technical — DF, high caps, almost no goals (clean sheet mentality)",
        "filters": {"position_in": ["DF"], "caps_range": (40, 999), "goals_range": (0, 5)},
    },
]

# ── DB helpers ────────────────────────────────────────────────────────────────

def _build_query(filters: dict, exclude_ids: list[int]) -> tuple[str, dict]:
    """Build a parameterised WHERE clause from slot filter criteria and an exclusion list."""
    conditions: list[str] = ["position IS NOT NULL"]
    params: dict[str, Any] = {}

    team_ph = ", ".join(f":team{i}" for i in range(len(QUIZ_TEAMS)))
    conditions.append(f"team IN ({team_ph})")
    for i, t in enumerate(QUIZ_TEAMS):
        params[f"team{i}"] = t

    if "position_in" in filters:
        ph = ", ".join(f":p{i}" for i in range(len(filters["position_in"])))
        conditions.append(f"position IN ({ph})")
        for i, p in enumerate(filters["position_in"]):
            params[f"p{i}"] = p

    if "caps_range" in filters:
        lo, hi = filters["caps_range"]
        conditions.append("caps BETWEEN :caps_lo AND :caps_hi")
        params["caps_lo"], params["caps_hi"] = lo, hi

    if "height_range" in filters:
        lo, hi = filters["height_range"]
        conditions.append("height_cm BETWEEN :height_lo AND :height_hi")
        params["height_lo"], params["height_hi"] = lo, hi

    if "goals_range" in filters:
        lo, hi = filters["goals_range"]
        conditions.append("goals BETWEEN :goals_lo AND :goals_hi")
        params["goals_lo"], params["goals_hi"] = lo, hi

    if exclude_ids:
        ph = ", ".join(f":ex{i}" for i in range(len(exclude_ids)))
        conditions.append(f"id NOT IN ({ph})")
        for i, eid in enumerate(exclude_ids):
            params[f"ex{i}"] = eid

    return " AND ".join(conditions), params


def find_slot_player(slot_filters: dict, exclude_ids: list[int], offset: int = 0) -> dict | None:
    """Return a player matching slot filters, skipping already-used players."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    where, params = _build_query(slot_filters, exclude_ids)
    row = conn.execute(
        f"SELECT * FROM players WHERE {where} ORDER BY RANDOM() LIMIT 1 OFFSET {offset}",
        params,
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def find_all_slot_players(slots: list[dict], personality: dict) -> list[dict]:
    """Find one player per slot, ensuring no duplicates."""
    used_ids: list[int] = []
    results  = []

    for slot in slots:
        filters = dict(slot["filters"])
        player  = find_slot_player(filters, used_ids)
        if player:
            used_ids.append(player["id"])
            results.append({"slot": slot, "player": player})
        else:
            results.append({"slot": slot, "player": None})

    return results
