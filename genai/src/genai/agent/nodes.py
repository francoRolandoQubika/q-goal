"""
LangGraph nodes — office-themed quiz with dynamically generated questions.

Graph flow per question:
  generate_question → wait_for_answer (interrupt) → interpret_answer → route

The generated question text is stored in state["current_question"] so the
API can read it from the state snapshot after the interrupt fires.
"""
from typing import Literal

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt

from genai.agent.questions import QUESTION_THEMES, NUM_QUESTIONS, OUTPUT_SLOTS, find_all_slot_players

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9)

SYSTEM_PROMPT = """Sos el animador de "Tu equipo del Mundial en la oficina" —
un juego que asigna jugadores del Mundial 2026 a situaciones de laburo en una software factory.
Hablás en español rioplatense (vos, che, dale) con humor tech y futbolero.
Sos conciso, directo y gracioso. Máximo 2-3 líneas por respuesta salvo que se pida más."""


# ── Nodes ─────────────────────────────────────────────────────────────────────

def intro(state: dict) -> dict:
    """Generate the opening monologue that sets up the quiz."""
    resp = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Hacé una intro corta (máx 3 líneas) para el juego. "
            f"Vas a hacer {NUM_QUESTIONS} preguntas de situaciones de oficina para armar "
            "el equipo ideal del Mundial: cada respuesta determina con qué jugador haría "
            "cada cosa en el trabajo. Generá expectativa, nada de spoilers."
        )),
    ])
    return {"messages": [AIMessage(content=resp.content)]}


def generate_question(state: dict) -> dict:
    """LLM generates a fresh, funny question for the current theme."""
    theme   = QUESTION_THEMES[state["q_index"]]
    q_num   = state["q_index"] + 1
    total   = NUM_QUESTIONS

    resp = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"Generá la pregunta {q_num} de {total}.\n"
            f"Tema: {theme['topic']}.\n"
            f"Contexto: {theme['hint']}.\n"
            "Requisitos:\n"
            "- Una situación concreta y divertida de una software factory argentina\n"
            "- 4 opciones (A, B, C, D) que reflejen personalidades distintas\n"
            "- Usá emojis para hacerlo visual\n"
            "- No repitas situaciones de preguntas anteriores\n"
            "- Solo la pregunta y las opciones, sin texto adicional"
        )),
    ])
    return {
        "current_question": resp.content,
        "messages": [AIMessage(content=resp.content)],
    }


def wait_for_answer(state: dict) -> dict:
    """Pause execution — API resumes this with the user's answer."""
    user_input = interrupt("awaiting_answer")
    return {"messages": [HumanMessage(content=user_input)]}


def interpret_answer(state: dict) -> dict:
    """LLM extracts a personality trait from the freeform answer."""
    question = state["current_question"]
    answer   = state["messages"][-1].content

    trait_resp = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Pregunta: {question}\n"
            f"Respuesta del usuario: '{answer}'\n"
            "En 3-5 palabras en inglés, describí el rasgo de personalidad que revela esta respuesta "
            "(ej: 'pragmatic team player', 'lone wolf perfectionist', 'chaotic deployer'). "
            "Solo las palabras, sin explicación."
        )),
    ])
    trait = trait_resp.content.strip()

    ack = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"El usuario respondió '{answer}' (rasgo detectado: {trait}). "
            "Reaccioná con 1 línea graciosa del mundo tech/oficina. "
            "No menciones el rasgo directamente."
        )),
    ])

    personality = {**state.get("personality", {}), f"q{state['q_index']}": trait}

    return {
        "messages":    [AIMessage(content=ack.content)],
        "personality": personality,
        "q_index":     state["q_index"] + 1,
    }


def route_questions(state: dict) -> Literal["generate_question", "build_team"]:
    """Route to build_team when all questions have been answered, else loop back."""
    return "build_team" if state["q_index"] >= NUM_QUESTIONS else "generate_question"


def build_team(state: dict) -> dict:
    """
    Assemble the final player assignments from accumulated personality traits.

    Queries the DB for one player per OUTPUT_SLOT (no duplicates), then asks the LLM
    to write a humorous outro that ties the user profile to the assigned players.
    """
    personality: dict = state.get("personality", {})
    assignments = find_all_slot_players(OUTPUT_SLOTS, personality)

    personality_summary = ", ".join(personality.values())
    slots_text = "\n".join(
        f"- {a['slot']['title']}: {a['player']['name'] if a['player'] else 'N/A'}"
        for a in assignments
    )

    outro = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"Perfil del usuario: {personality_summary}\n"
            f"Equipo asignado:\n{slots_text}\n\n"
            "Escribí una conclusión divertida (máx 4 líneas) cruzando el mundo del software "
            "con el fútbol. Hacé referencia al perfil y a los jugadores."
        )),
    ])

    return {
        "messages": [AIMessage(content=outro.content)],
        "assignments": [
            {"title": a["slot"]["title"], "player": a["player"]}
            for a in assignments
        ],
    }
