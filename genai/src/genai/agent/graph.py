"""
LangGraph graph definition and session helpers for the office-quiz agent.

Compiles the StateGraph (intro → generate_question → wait_for_answer → interpret_answer
→ route → build_team) with MemorySaver checkpointing and exposes start_session /
submit_answer helpers consumed by the FastAPI endpoints.
"""
import operator
from typing import Annotated

from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from genai.agent.nodes import (
    intro,
    generate_question,
    wait_for_answer,
    interpret_answer,
    route_questions,
    build_team,
)


class AgentState(dict):
    messages:          Annotated[list[BaseMessage], operator.add]
    personality:       dict
    q_index:           int
    current_question:  str
    assignments:       list | None


_graph = None


def build_graph():
    """Build and compile the LangGraph quiz graph (singleton — built once per process)."""
    global _graph
    if _graph is not None:
        return _graph

    g = StateGraph(AgentState)

    g.add_node("intro",             intro)
    g.add_node("generate_question", generate_question)
    g.add_node("wait_for_answer",   wait_for_answer)
    g.add_node("interpret_answer",  interpret_answer)
    g.add_node("build_team",        build_team)

    g.set_entry_point("intro")
    g.add_edge("intro",             "generate_question")
    g.add_edge("generate_question", "wait_for_answer")
    g.add_edge("wait_for_answer",   "interpret_answer")
    g.add_conditional_edges("interpret_answer", route_questions)
    g.add_edge("build_team", END)

    _graph = g.compile(checkpointer=MemorySaver())
    return _graph


# ── Helpers used by API ───────────────────────────────────────────────────────

INITIAL_STATE = {
    "messages":         [],
    "personality":      {},
    "q_index":          0,
    "current_question": "",
    "assignments":      None,
}


def _config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def start_session(session_id: str) -> dict:
    """Kick off a new quiz session. Runs until the first interrupt."""
    graph = build_graph()
    for _ in graph.stream(INITIAL_STATE, _config(session_id), stream_mode="values"):
        pass
    return graph.get_state(_config(session_id)).values


def submit_answer(session_id: str, answer: str) -> dict:
    """Resume an interrupted session with the user's answer."""
    graph = build_graph()
    for _ in graph.stream(Command(resume=answer), _config(session_id), stream_mode="values"):
        pass
    return graph.get_state(_config(session_id)).values


def is_complete(state: dict) -> bool:
    """Return True when the quiz has finished and player assignments are available."""
    return state.get("assignments") is not None


# ── CLI ───────────────────────────────────────────────────────────────────────

def run_cli():
    """Interactive CLI loop for the office-quiz agent."""
    import uuid
    session_id = str(uuid.uuid4())

    print("\n" + "="*60)
    print("  Tu equipo del Mundial 2026 en la oficina ⚽💻")
    print("="*60 + "\n")

    state = start_session(session_id)
    msgs  = state.get("messages", [])
    if msgs and isinstance(msgs[-1], AIMessage):
        print(f"🤖  {msgs[-1].content}\n")

    while not is_complete(state):
        answer = input("👤  Tu respuesta: ").strip()
        state  = submit_answer(session_id, answer)

        msgs = state.get("messages", [])
        for msg in msgs[-2:]:
            if isinstance(msg, AIMessage):
                print(f"\n🤖  {msg.content}")
        print()

    print("\n" + "="*60)
    print("  TU EQUIPO DEL MUNDIAL EN LA OFICINA")
    print("="*60)
    for a in state.get("assignments", []):
        p = a["player"]
        if not p:
            continue
        print(f"\n{a['title']}")
        print(f"  {p['name']} · {p['team'].replace('_', ' ').title()} · {p.get('caps', '?')} partidos")
    print("="*60 + "\n")
