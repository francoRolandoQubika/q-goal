"""
Enrich players.db with stats from statsFifa.pdf.
Adds: position, dob, club, height_cm, caps, goals.

The PDF has variable column counts (13-15) per page. We parse the header
row dynamically to find column indices, then extract data accordingly.
"""
import re
import sys
import sqlite3
import unicodedata
import pdfplumber
from difflib import SequenceMatcher
from pathlib import Path

from genai.core.config import DATA_DIR, STATS_PDF

PDF_PATH = STATS_PDF
DB_FILE  = str(DATA_DIR / "players.db")

TEAM_MAP = {
    "Algeria": "algeria",
    "Argentina": "argentina",
    "Australia": "australia",
    "Austria": "austria",
    "Belgium": "belgium",
    "Bosnia And Herzegovina": "bosnia_and_herzegovina",
    "Brazil": "brazil",
    "Cabo Verde": "cabo_verde",
    "Canada": "canada",
    "Colombia": "colombia",
    "Congo Dr": "congo_dr",
    "Côte D'Ivoire": "cote_divoire",
    "Cote D'Ivoire": "cote_divoire",
    "Croatia": "croatia",
    "Curaçao": "curacao",
    "Curacao": "curacao",
    "Czechia": "czechia",
    "Ecuador": "ecuador",
    "Egypt": "egypt",
    "England": "england",
    "France": "france",
    "Germany": "germany",
    "Ghana": "ghana",
    "Haiti": "haiti",
    "Ir Iran": "ir_iran",
    "Iraq": "iraq",
    "Japan": "japan",
    "Jordan": "jordan",
    "Korea Republic": "korea_republic",
    "Mexico": "mexico",
    "Morocco": "morocco",
    "Netherlands": "netherlands",
    "New Zealand": "new_zealand",
    "Norway": "norway",
    "Panama": "panama",
    "Paraguay": "paraguay",
    "Portugal": "portugal",
    "Qatar": "qatar",
    "Saudi Arabia": "saudi_arabia",
    "Scotland": "scotland",
    "Senegal": "senegal",
    "South Africa": "south_africa",
    "Spain": "spain",
    "Sweden": "sweden",
    "Switzerland": "switzerland",
    "Tunisia": "tunisia",
    "Türkiye": "turkiye",
    "Turkey": "turkiye",
    "Uruguay": "uruguay",
    "Usa": "usa",
    "Uzbekistan": "uzbekistan",
}

COL_ALIASES = {
    "#": {"#"},
    "POS": {"POS"},
    "PLAYER NAME": {"PLAYER NAME"},
    "FIRST NAME(S)": {"FIRST NAME(S)", "FIRST NAME"},
    "LAST NAME(S)": {"LAST NAME(S)", "LAST NAME"},
    "NAME ON SHIRT": {"NAME ON SHIRT"},
    "DOB": {"DOB"},
    "CLUB": {"CLUB"},
    "HEIGHT (CM)": {"HEIGHT (CM)", "HEIGHT(CM)"},
    "CAPS": {"CAPS"},
    "GOALS": {"GOALS"},
}


def normalize_ascii(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


def normalize_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize_ascii(s))


def find_col(header_row: list, target: str) -> int | None:
    aliases = COL_ALIASES.get(target, {target})
    for i, cell in enumerate(header_row):
        if cell and str(cell).strip().upper() in {a.upper() for a in aliases}:
            return i
    return None


def get_col(row: list, idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return str(row[idx] or "").strip()


def extract_team_from_page(page_text: str) -> str | None:
    for line in page_text.splitlines():
        line = line.strip()
        m = re.match(r"^(.+?)\s+\([A-Z]{3}\)$", line)
        if m:
            return m.group(1).strip()
    return None


def pdf_name_to_db(first_names: str, last_names: str) -> list[str]:
    fn0     = first_names.strip().split()[0].title() if first_names.strip() else ""
    fn_full = " ".join(w.title() for w in first_names.strip().split())
    ln      = " ".join(w.title() for w in last_names.strip().split())
    candidates = []
    if fn0 and ln:
        candidates.append(f"{fn0} {ln}")
    if fn_full and ln:
        candidates.append(f"{fn_full} {ln}")
    if fn0:
        candidates.append(fn0)
    return candidates


def best_match(names: list[str], candidates: list[tuple[int, str]], threshold=0.75):
    best_score, best_id, best_name = 0.0, None, None
    for pid, pname in candidates:
        for try_name in names:
            score = SequenceMatcher(
                None, normalize_key(try_name), normalize_key(pname)
            ).ratio()
            if score > best_score:
                best_score, best_id, best_name = score, pid, pname
    if best_score >= threshold:
        return best_id, best_score, best_name
    return None, best_score, best_name


def parse_pdf() -> dict[str, list[dict]]:
    """Parse statsFifa.pdf and return a dict mapping team_slug → list of player stat dicts."""
    result = {}
    with pdfplumber.open(PDF_PATH) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            raw_team = extract_team_from_page(text)
            if not raw_team:
                print(f"  [WARN] Page {i+1}: could not find team name")
                continue

            team_slug = TEAM_MAP.get(raw_team) or TEAM_MAP.get(raw_team.title())
            if not team_slug:
                for key, val in TEAM_MAP.items():
                    if normalize_key(key) == normalize_key(raw_team):
                        team_slug = val
                        break
            if not team_slug:
                print(f"  [WARN] Page {i+1}: no mapping for '{raw_team}'")
                continue

            tables = page.extract_tables()
            if not tables:
                print(f"  [WARN] Page {i+1} ({raw_team}): no table")
                continue

            table = tables[0]
            header_row = None
            header_idx = 0
            for ri, row in enumerate(table):
                if row and any(str(c or "").strip() == "#" for c in row):
                    header_row = row
                    header_idx = ri
                    break

            if header_row is None:
                print(f"  [WARN] Page {i+1} ({raw_team}): no header row found")
                continue

            ci = {
                "pos":    find_col(header_row, "POS"),
                "fn":     find_col(header_row, "FIRST NAME(S)"),
                "ln":     find_col(header_row, "LAST NAME(S)"),
                "shirt":  find_col(header_row, "NAME ON SHIRT"),
                "dob":    find_col(header_row, "DOB"),
                "club":   find_col(header_row, "CLUB"),
                "ht":     find_col(header_row, "HEIGHT (CM)"),
                "caps":   find_col(header_row, "CAPS"),
                "goals":  find_col(header_row, "GOALS"),
                "player": find_col(header_row, "PLAYER NAME"),
            }

            players = []
            for row in table[header_idx + 1:]:
                if not row or not row[0]:
                    continue
                num = str(row[0]).strip()
                if not num.isdigit():
                    continue

                pos   = get_col(row, ci["pos"])
                fn    = get_col(row, ci["fn"])
                ln    = get_col(row, ci["ln"])
                shirt = get_col(row, ci["shirt"])
                dob   = get_col(row, ci["dob"])
                club  = get_col(row, ci["club"])
                ht    = get_col(row, ci["ht"])
                caps  = get_col(row, ci["caps"])
                goals = get_col(row, ci["goals"])
                player = get_col(row, ci["player"])

                if not pos:
                    continue

                name_candidates = pdf_name_to_db(fn, ln)
                if shirt and shirt not in name_candidates:
                    name_candidates.append(shirt.title())
                if player:
                    parts = player.strip().split()
                    if len(parts) >= 2:
                        name_candidates.append(
                            f"{parts[-1].title()} {' '.join(p.title() for p in parts[:-1])}"
                        )
                        name_candidates.append(" ".join(p.title() for p in parts))

                players.append({
                    "pos":       pos,
                    "dob":       dob,
                    "club":      club,
                    "height_cm": int(ht) if ht.isdigit() else None,
                    "caps":      int(caps) if caps.isdigit() else None,
                    "goals":     int(goals) if goals.isdigit() else None,
                    "names":     name_candidates,
                    "raw":       f"{fn} / {ln}",
                })

            result[team_slug] = players
            print(f"  Page {i+1}: {raw_team} → {team_slug} ({len(players)} players)")

    return result


def enrich(pdf_data: dict[str, list[dict]]):
    """Write parsed PDF stats into players.db."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()}
    new_cols = {
        "position":  "TEXT",
        "dob":       "TEXT",
        "club":      "TEXT",
        "height_cm": "INTEGER",
        "caps":      "INTEGER",
        "goals":     "INTEGER",
    }
    for col, ctype in new_cols.items():
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE players ADD COLUMN {col} {ctype}")
            print(f"  Added column: {col}")
    conn.commit()

    total_matched   = 0
    total_unmatched = 0

    for team_slug, pdf_players in pdf_data.items():
        db_players = conn.execute(
            "SELECT id, name FROM players WHERE team = ?", (team_slug,)
        ).fetchall()

        if not db_players:
            print(f"  [SKIP] No DB players for team '{team_slug}'")
            continue

        db_candidates = [(r["id"], r["name"]) for r in db_players]

        for pp in pdf_players:
            pid, score, matched_db = best_match(pp["names"], db_candidates)

            if pid is not None:
                conn.execute(
                    """UPDATE players
                       SET position=?, dob=?, club=?, height_cm=?, caps=?, goals=?
                       WHERE id=?""",
                    (pp["pos"], pp["dob"], pp["club"], pp["height_cm"],
                     pp["caps"], pp["goals"], pid),
                )
                total_matched += 1
            else:
                print(f"  [NOMATCH] {team_slug:<25s}  {pp['raw']!r}  (best={score:.2f})")
                total_unmatched += 1

    conn.commit()
    conn.close()
    print(f"\nDone — matched {total_matched}, unmatched {total_unmatched}")


def main():
    if not Path(PDF_PATH).is_file():
        print(f"[enrich] ERROR: stats PDF not found at {PDF_PATH}")
        print("         Place statsFifa.pdf in genai/ or set STATS_PDF=/path/to/file.pdf")
        sys.exit(1)

    if not Path(DB_FILE).is_file():
        print(f"[enrich] ERROR: players.db not found at {DB_FILE}")
        print("         Run the db step first: uv run genai-pipeline --steps db")
        sys.exit(1)

    conn = sqlite3.connect(DB_FILE)
    existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(players)").fetchall()}
    if "position" in existing_cols:
        conn.execute("UPDATE players SET position=NULL, dob=NULL, club=NULL, height_cm=NULL, caps=NULL, goals=NULL")
        conn.commit()
    conn.close()

    print("Parsing PDF...")
    pdf_data = parse_pdf()
    total_pdf = sum(len(v) for v in pdf_data.values())
    print(f"\nExtracted {total_pdf} players from {len(pdf_data)} teams")
    print("\nEnriching DB...")
    enrich(pdf_data)


if __name__ == "__main__":
    main()
