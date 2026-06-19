"""
FIFA World Cup 2026 - Player photo scraper
Downloads a headshot for every player in all 48 squads.
Output: {DATA_DIR}/players/{team_slug}/{player_name}.jpg
"""
import json
import time
import requests
from pathlib import Path

from genai.core.config import DATA_DIR

TEAMS_URL = (
    "https://cxm-api.fifa.com/fifaplusweb/api/sections/"
    "teamsModule/4v5Yng3VdGD9c1cpnOIff1?locale=en&limit=48"
)
SQUAD_URL = (
    "https://api.fifa.com/api/v3/teams/{team_id}/squad"
    "?idCompetition=17&idSeason=285023&language=en"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

OUTPUT_DIR = DATA_DIR / "players"


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace(".", "").replace("'", "")


def fetch_teams() -> list[dict]:
    r = requests.get(TEAMS_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    teams = r.json()["teams"]
    print(f"Found {len(teams)} teams")
    return teams


def fetch_squad(team_id: str) -> list[dict]:
    url = SQUAD_URL.format(team_id=team_id)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json().get("Players", [])


def download_photo(player: dict, dest: Path) -> bool:
    pic = player.get("PlayerPicture")
    if not pic:
        return False
    url = pic.get("PictureUrl")
    if not url:
        return False

    try:
        r = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        if r.status_code != 200:
            return False
        content_type = r.headers.get("content-type", "")
        ext = ".jpg" if "jpeg" in content_type or "jpg" in content_type else ".png"
        out_path = dest.with_suffix(ext)
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"    [error] {e}")
        return False


def get_player_name(player: dict) -> str:
    names = player.get("PlayerName", [])
    for n in names:
        if n.get("Locale") == "en-GB":
            return n["Description"]
    return names[0]["Description"] if names else f"player_{player['IdPlayer']}"


def save_manifest(manifest: list[dict]):
    with open(DATA_DIR / "players_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest saved → players_manifest.json ({len(manifest)} players)")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    teams = fetch_teams()
    manifest = []
    total_ok = 0
    total_missing = 0

    for team in teams:
        team_id   = team["teamId"]
        team_name = team["teamName"]
        team_slug = slugify(team_name)
        team_dir  = OUTPUT_DIR / team_slug
        team_dir.mkdir(exist_ok=True)

        print(f"\n{team_name} ({team_id})")
        try:
            players = fetch_squad(team_id)
        except Exception as e:
            print(f"  [squad error] {e}")
            continue

        for player in players:
            name  = get_player_name(player)
            dest  = team_dir / slugify(name)
            entry = {
                "team":       team_name,
                "team_id":    team_id,
                "player_id":  player["IdPlayer"],
                "name":       name,
                "jersey":     player.get("JerseyNum"),
                "position":   player.get("RealPositionLocalized", [{}])[0].get("Description"),
                "photo_path": None,
            }

            if download_photo(player, dest):
                for ext in (".jpg", ".png"):
                    p = dest.with_suffix(ext)
                    if p.exists():
                        entry["photo_path"] = str(p)
                        break
                print(f"  ✓ {name}")
                total_ok += 1
            else:
                print(f"  ✗ {name} (no photo)")
                total_missing += 1

            manifest.append(entry)
            time.sleep(0.1)

        time.sleep(0.5)

    save_manifest(manifest)
    print(f"\nDone. Downloaded: {total_ok} | Missing: {total_missing}")


if __name__ == "__main__":
    main()
