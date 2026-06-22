def main() -> None:
    """Entry point for `uv run genai` — starts the face-match + quiz API."""
    from genai.api import serve
    serve()
