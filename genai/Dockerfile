FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install ML + API dependencies (pinned to tested versions).
# NOTE: kept as an explicit list rather than `uv pip install -r pyproject.toml`
# because the loose `>=` constraints resolve differently under uv and drag in an
# ancient rembg->numba->llvmlite chain (llvmlite 0.36.0) that has no py3.13/arm64
# wheel and fails to build. If single-sourcing, switch to `uv sync --frozen` with
# the committed uv.lock (exact pins), not a fresh `>=` resolve. Keep in sync with
# genai/pyproject.toml — notably python-multipart, required by the /match route.
RUN pip install --no-cache-dir \
    "deepface>=0.0.100" \
    "fastapi>=0.137" \
    "insightface>=1.0" \
    "langchain-core>=1.4" \
    "langchain-openai>=1.3" \
    "langgraph>=1.2" \
    "numpy>=2.4" \
    "onnxruntime>=1.27" \
    "openai>=2.43" \
    "pdfplumber>=0.11" \
    "pillow>=12" \
    "python-dotenv>=1.0" \
    "python-multipart>=0.0.32" \
    "rembg>=2.0" \
    "requests>=2.34" \
    "torch>=2.12" \
    "torchvision>=0.27" \
    "transformers>=5.12" \
    "uvicorn>=0.49"

# Copy source only — data files (players.db, embeddings*.npy, faces/) come from volumes
COPY genai/src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8002

# DATA_DIR resolves to /app/ (parents[2] of /app/src/genai/api.py)
# so volume mounts at /app/players.db, /app/faces, /app/embeddings*.npy are found automatically
CMD ["python", "-m", "genai.api"]
