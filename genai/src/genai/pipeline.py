"""
WC2026 Face Match — full ETL pipeline
======================================
Runs every step needed to go from scratch to a running API.

Steps:
  1. scrape      Download player photos from FIFA API → {DATA_DIR}/players/
  2. crop        Detect & crop faces, remove background → {DATA_DIR}/faces/
  3. embed       Generate embeddings for each model    → {DATA_DIR}/embeddings*.npy
  4. db          Bootstrap SQLite DB from embeddings   → {DATA_DIR}/players.db
  5. enrich      Add player stats from PDF             → players.db (enriched)

Usage:
  python -m genai.pipeline                          # run all steps
  python -m genai.pipeline --steps scrape crop      # run specific steps only
  python -m genai.pipeline --models clip            # only build clip embeddings
  python -m genai.pipeline --force                  # re-run even if outputs exist
  python -m genai.pipeline --stats-pdf /path/to/statsFifa.pdf
"""
import argparse
import subprocess
import sys
import time
import sqlite3
from pathlib import Path

from genai.core.config import DATA_DIR, STATS_PDF as DEFAULT_STATS_PDF

PYTHON = sys.executable

ALL_STEPS  = ["scrape", "crop", "embed", "db", "enrich"]
ALL_MODELS = ["facenet", "clip"]

DEFAULT_PDF = Path(DEFAULT_STATS_PDF) if DEFAULT_STATS_PDF else None


def banner(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def run(cmd: list[str], step: str):
    banner(f"STEP: {step}")
    print(f"  $ {' '.join(cmd)}\n")
    t0     = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"\n[FAIL] {step} exited with code {result.returncode}")
        sys.exit(result.returncode)
    print(f"\n[OK] {step} done in {elapsed:.1f}s")


def players_exist() -> bool:
    p = DATA_DIR / "players"
    return p.exists() and (any(p.rglob("*.jpg")) or any(p.rglob("*.png")))


def faces_exist() -> bool:
    f = DATA_DIR / "faces"
    return f.exists() and any(f.rglob("*.jpg"))


def embedding_exists(model: str) -> bool:
    files = {
        "facenet":     DATA_DIR / "embeddings.npy",
        "clip":        DATA_DIR / "embeddings_clip.npy",
        "insightface": DATA_DIR / "embeddings_insightface.npy",
    }
    return files[model].is_file()


def db_exists() -> bool:
    return (DATA_DIR / "players.db").exists()


def db_is_enriched() -> bool:
    if not db_exists():
        return False
    conn = sqlite3.connect(str(DATA_DIR / "players.db"))
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM players WHERE position IS NOT NULL"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        # position column doesn't exist yet — enrich hasn't run
        count = 0
    finally:
        conn.close()
    return count > 0


def main():
    parser = argparse.ArgumentParser(description="WC2026 face match ETL pipeline")
    parser.add_argument(
        "--steps", nargs="+", choices=ALL_STEPS, default=ALL_STEPS,
        metavar="STEP",
        help=f"Steps to run (default: all). Choices: {ALL_STEPS}",
    )
    parser.add_argument(
        "--models", nargs="+", choices=ALL_MODELS, default=ALL_MODELS,
        metavar="MODEL",
        help=f"Embedding models to build (default: all). Choices: {ALL_MODELS}",
    )
    parser.add_argument(
        "--stats-pdf", type=Path, default=DEFAULT_PDF,
        help="Path to statsFifa.pdf for the enrich step",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-run steps even if outputs already exist",
    )
    args   = parser.parse_args()
    steps  = args.steps
    t_total = time.time()

    if "scrape" in steps:
        if not args.force and players_exist():
            banner("STEP: scrape  [SKIP — players/ already populated]")
        else:
            run([PYTHON, "-m", "genai.etl.scraper"], "scrape")

    if "crop" in steps:
        if not args.force and faces_exist():
            banner("STEP: crop  [SKIP — faces/ already populated]")
        else:
            run([PYTHON, "-m", "genai.etl.crop"], "crop")

    if "embed" in steps:
        for model in args.models:
            if not args.force and embedding_exists(model):
                banner(f"STEP: embed ({model})  [SKIP — embedding file exists]")
            else:
                run([PYTHON, "-m", "genai.etl.embeddings", "--model", model], f"embed ({model})")

    if "db" in steps:
        if not args.force and db_exists():
            banner("STEP: db  [SKIP — players.db already exists]")
        else:
            run(
                [PYTHON, "-c",
                 "from genai.core.db import get_conn; get_conn(); print('[db] players.db built')"],
                "db",
            )

    if "enrich" in steps:
        if not args.force and db_is_enriched():
            banner("STEP: enrich  [SKIP — DB already enriched]")
        else:
            pdf = args.stats_pdf
            if not pdf or not pdf.exists():
                print(f"\n[WARN] Stats PDF not found at {pdf}")
                print("       Skipping enrich step. Re-run with --stats-pdf /path/to/file.pdf")
            else:
                import os
                env = os.environ.copy()
                env["STATS_PDF"] = str(pdf)
                banner("STEP: enrich")
                print(f"  $ STATS_PDF={pdf} {PYTHON} -m genai.etl.enrich\n")
                t0     = time.time()
                result = subprocess.run([PYTHON, "-m", "genai.etl.enrich"], env=env)
                if result.returncode != 0:
                    print(f"\n[FAIL] enrich exited with code {result.returncode}")
                    sys.exit(result.returncode)
                print(f"\n[OK] enrich done in {time.time()-t0:.1f}s")

    banner(f"PIPELINE COMPLETE in {time.time()-t_total:.1f}s")
    print("  Start the API with:  uv run genai-api\n")


if __name__ == "__main__":
    main()
