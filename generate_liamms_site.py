from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from next_smash_mains_profiles import (
    MATCHUP_DF,
    MODELS_DIR,
    RECORDS_DIR,
    ROOT,
    ROUND_DISPLAY,
    LABEL_TO_ROUND,
    build_profiles,
    build_opponent_profiles,
    compute_difficulty,
    _find_model_image,
)

PAGES_REPO_DIR = ROOT.parent / "liammspandasprojects"
SITE_DIR = PAGES_REPO_DIR if PAGES_REPO_DIR.exists() else ROOT / "LiamMs_PandasProjects"
ASSETS_DIR = SITE_DIR / "assets"
DATA_DIR = ASSETS_DIR / "data"
MODELS_OUT_DIR = ASSETS_DIR / "models"
ICONS_OUT_DIR = ASSETS_DIR / "icons"
SSBU_ICONS_DIR = ROOT / "ssbuicons"
SMASH_DIR = SITE_DIR / "Smash"
PDF_SOURCE_DIR = ROOT / "reports" / "next_smash_mains_reports" / "character_profiles"
PDF_OUT_DIR = ASSETS_DIR / "profile_pdfs"
ICON_SHEET_CANDIDATES = [
  ROOT / "character_icons.png",
  ROOT / "character_icons_sheet.png",
  ROOT / "smash_character_icons.png",
  ROOT / "smash_icons.png",
]
ICON_SHEET_COLUMNS = 8
ICON_SHEET_ORDER = [
  "Mario", "Donkey Kong", "Link", "Samus", "Yoshi", "Kirby", "Fox", "Pikachu",
  "Pichu", "Luigi", "Ness", "Captain Falcon", "Jigglypuff", "Peach", "Bowser", "Ice Climbers",
  "Sheik", "Zelda", "Dr Mario", "Falco", "Marth", "Lucina", "Young Link", "Ganondorf",
  "Mewtwo", "Roy", "Chrom", "Meta Knight", "Pit", "Zero Suit Samus", "Wario", "Snake",
  "Ike", "Pokemon Trainer", "Diddy Kong", "Lucas", "Sonic", "King Dedede", "Olimar", "Lucario",
  "ROB", "Toon Link", "Wolf", "Villager", "Mega Man", "Wii Fit Trainer", "Rosalina & Luma", "Little Mac",
  "Greninja", "Mii Brawler", "Mii Swordfighter", "Mii Gunner", "Palutena", "PacMan", "Robin", "Shulk",
  "Bowser Jr", "Duck Hunt", "Ryu", "Ken", "Cloud", "Corrin", "Bayonetta", "Inkling",
  "Ridley", "Simon", "Richter", "King K Rool", "Isabelle", "Incineroar", "Piranha Plant", "Joker",
  "Hero", "Banjo & Kazooie", "Terry", "Byleth", "Min Min", "Steve", "Sephiroth", "Pyra & Mythra",
  "Kazuya", "Sora",
]
DISPLAY_NAME_OVERRIDES = {
    "Mii Swordfighter": "That Girl",
    "Mii Gunner": "Panda",
    "Mii Brawler": "Thunk",
}


def display_name(name: str) -> str:
    return DISPLAY_NAME_OVERRIDES.get(name, name)


def icon_asset_stem(name: str) -> str:
  overrides = {
    "Banjo & Kazooie": "BanjoAndKazooie",
    "Bowser Jr": "BowserJr",
    "Captain Falcon": "CaptainFalcon",
    "Dark Pit": "DarkPit",
    "Dark Samus": "DarkSamus",
    "Diddy Kong": "DiddyKong",
    "Donkey Kong": "DonkeyKong",
    "Dr Mario": "DrMario",
    "Duck Hunt": "DuckHunt",
    "Ice Climbers": "IceClimbersPopo",
    "King Dedede": "KingDedede",
    "King K Rool": "KingKRool",
    "Little Mac": "LittleMac",
    "Mega Man": "MegaMan",
    "Meta Knight": "MetaKnight",
    "Mii Brawler": "MiiBrawler",
    "Mii Gunner": "MiiGunner",
    "Mii Swordfighter": "MiiSwordfighter",
    "Min Min": "MinMin",
    "Mr Game & Watch": "MrGameAndWatch",
    "Mr Game and Watch": "MrGameAndWatch",
    "PacMan": "Pac-Man",
    "Piranha Plant": "PiranhaPlant",
    "Pokemon Trainer": "PokemonTrainer",
    "Pyra & Mythra": "Pyra",
    "ROB": "Rob",
    "Rosalina & Luma": "Rosalina",
    "Toon Link": "ToonLink",
    "Wii Fit Trainer": "WiiFitTrainer",
    "Young Link": "YoungLink",
    "Zero Suit Samus": "ZeroSuitSamus",
  }
  return overrides.get(name, "".join(ch for ch in name if ch.isalnum()))


def slugify(name: str) -> str:
    replacements = {
        "&": "and",
        ".": "",
        "'": "",
    }
    value = name
    for old, new in replacements.items():
        value = value.replace(old, new)
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-")


def safe_profile_file(name: str) -> str:
    return name.replace(" & ", "_and_").replace(" ", "_").replace("/", "_") + "_profile.pdf"


def rel(from_dir: Path, to_path: Path) -> str:
    return Path(to_path).relative_to(from_dir).as_posix() if to_path.is_relative_to(from_dir) else to_path.as_posix()


def ensure_dirs() -> None:
    for path in [SITE_DIR, ASSETS_DIR, DATA_DIR, MODELS_OUT_DIR, ICONS_OUT_DIR, SMASH_DIR, PDF_OUT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def copy_model_asset(name: str) -> str | None:
    source = _find_model_image(name, MODELS_DIR)
    if source is None:
        return None
    destination = MODELS_OUT_DIR / f"{slugify(name)}.webp"
    if destination.exists() and source.stat().st_mtime <= destination.stat().st_mtime:
        return f"assets/models/{destination.name}"
    try:
        from PIL import Image
    except ImportError:
        destination = MODELS_OUT_DIR / source.name
        if not destination.exists() or source.stat().st_mtime > destination.stat().st_mtime:
            shutil.copy2(source, destination)
        return f"assets/models/{destination.name}"

    image = Image.open(source).convert("RGBA")
    image.thumbnail((900, 900), Image.LANCZOS)
    image.save(destination, "WEBP", quality=82, method=6)
    return f"assets/models/{destination.name}"


def copy_pdf_asset(name: str) -> str | None:
    source = PDF_SOURCE_DIR / safe_profile_file(name)
    if not source.exists():
        return None
    destination = PDF_OUT_DIR / source.name
    if not destination.exists() or source.stat().st_mtime > destination.stat().st_mtime:
        shutil.copy2(source, destination)
    return f"assets/profile_pdfs/{destination.name}"


def crop_icon_sheet() -> None:
    source = next((path for path in ICON_SHEET_CANDIDATES if path.exists()), None)
    if source is None:
        return
    try:
        from PIL import Image
    except ImportError:
        print("Character icon sheet found, but Pillow is not installed; skipping icon crop.")
        return

    image = Image.open(source).convert("RGBA")
    rows = (len(ICON_SHEET_ORDER) + ICON_SHEET_COLUMNS - 1) // ICON_SHEET_COLUMNS
    cell_width = image.width // ICON_SHEET_COLUMNS
    cell_height = image.height // rows
    for index, name in enumerate(ICON_SHEET_ORDER):
        col = index % ICON_SHEET_COLUMNS
        row = index // ICON_SHEET_COLUMNS
        left = col * cell_width
        top = row * cell_height
        icon = image.crop((left, top, left + cell_width, top + cell_height))
        icon.save(ICONS_OUT_DIR / f"{slugify(name)}.png")


def copy_first_ssbu_icons(names: list[str]) -> None:
    if not SSBU_ICONS_DIR.exists():
        return
    for name in names:
        stem = icon_asset_stem(name)
        candidates = sorted(SSBU_ICONS_DIR.glob(f"{stem}0.png")) or sorted(SSBU_ICONS_DIR.glob(f"{stem}1.png"))
        if not candidates:
            candidates = sorted(SSBU_ICONS_DIR.glob(f"{stem}*.png"))
        if not candidates:
            continue
        destination = ICONS_OUT_DIR / f"{slugify(name)}.png"
        shutil.copy2(candidates[0], destination)



def create_fallback_icons(names: list[str]) -> None:
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFont
    except ImportError:
        return

    for name in names:
        destination = ICONS_OUT_DIR / f"{slugify(name)}.png"
        if destination.exists():
            continue
        model = _find_model_image(name, MODELS_DIR)
        if model and model.exists():
            image = Image.open(model).convert("RGBA")
            size = min(image.size)
            left = max(0, (image.width - size) // 2)
            top = max(0, (image.height - size) // 5)
            image = image.crop((left, top, left + size, top + size)).resize((180, 180), Image.LANCZOS)
            mask = Image.new("L", (180, 180), 0)
            ImageDraw.Draw(mask).ellipse((6, 6, 174, 174), fill=255)
            image.putalpha(ImageChops.multiply(image.getchannel("A"), mask))
            image.save(destination)
            continue
        image = Image.new("RGBA", (180, 180), (16, 27, 45, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 172, 172), fill=(18, 31, 52, 235), outline=(0, 200, 255, 190), width=4)
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except OSError:
            font = ImageFont.load_default()
        initial = display_name(name)[:1]
        bbox = draw.textbbox((0, 0), initial, font=font)
        draw.text(((180 - (bbox[2] - bbox[0])) / 2, (180 - (bbox[3] - bbox[1])) / 2 - 8), initial, fill=(232, 237, 246, 230), font=font)
        image.save(destination)


def copy_icon_asset(name: str) -> str | None:
    source = ICONS_OUT_DIR / f"{slugify(name)}.png"
    if not source.exists():
        return None
    return f"assets/icons/{source.name}"


def round_score_totals(profile) -> dict[str, float]:
    totals: dict[str, float] = {}
    for match in profile.matches:
        label = match["round_label"]
        totals[label] = totals.get(label, 0.0) + float(match["Score"])
    return {label: round(score, 3) for label, score in totals.items()}


def match_points(profile) -> list[dict[str, object]]:
    points = []
    for match in profile.matches:
        label = match["round_label"]
        display = ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 0), label)
        points.append(
            {
                "round": display,
                "roundLabel": label,
                "match": int(match["Round"]),
                "opponent": str(match["Opponent"]),
                "score": round(float(match["Score"]), 3),
                "accumulatedScore": round(float(match["Accumulated_Sum"]), 3),
            }
        )
    return points

def opponent_payload(opp_profile) -> dict[str, object]:
    """Serialise an OpponentProfile into a JSON-safe dict for the website."""
    appearances = [
        {
            "round": ROUND_DISPLAY.get(LABEL_TO_ROUND.get(a["round_label"], 0), a["round_label"]),
            "roundLabel": a["round_label"],
            "matchNum": a["round_num"],
            "against": a["against"],
            "stockDiff": a["opp_stock_diff"],
            "percentage": a["percentage"],
            "ntScore": a["nt_score"],
            "win": a["win"],
        }
        for a in opp_profile.appearances
    ]
    round_totals = [
        {
            "round": ROUND_DISPLAY.get(LABEL_TO_ROUND.get(lbl, 0), lbl),
            "roundLabel": lbl,
            "ntScore": score,
        }
        for lbl, score in opp_profile.nt_score_by_round.items()
    ]
    return {
        "totalAppearances": opp_profile.total_appearances,
        "wins": opp_profile.wins,
        "losses": opp_profile.losses,
        "winRate": round(opp_profile.win_rate, 4),
        "totalNtScore": opp_profile.total_nt_score,
        "avgNtScore": opp_profile.avg_nt_score,
        "appearances": appearances,
        "roundTotals": round_totals,
    }


def profile_payload(profile, all_profiles: dict[str, object], opponent_profiles: dict[str, object] | None = None, difficulty_map: dict[str, float] | None = None) -> dict[str, object]:
    wins = sum(1 for match in profile.matches if match["Win"])
    total = len(profile.matches)
    raw_lost = round(sum(profile.lost_score_per_rescoring.values()), 3)
    adjusted_lost = round(sum(profile.adjusted_lost_score_per_rescoring.values()), 3)
    model_path = copy_model_asset(profile.name)
    icon_path = copy_icon_asset(profile.name)
    pdf_path = copy_pdf_asset(profile.name)

    ranks = [
        {
            "round": ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 0), label),
            "roundLabel": label,
            "rank": rank,
            "score": round(profile.scores_by_round.get(label, 0.0), 3),
        }
        for label, rank in profile.ranks_by_round.items()
    ]
    round_totals = [
        {
            "round": ROUND_DISPLAY.get(LABEL_TO_ROUND.get(label, 0), label),
            "roundLabel": label,
            "score": score,
        }
        for label, score in round_score_totals(profile).items()
    ]

    opp_data = (
        opponent_payload(opponent_profiles[profile.name])
        if opponent_profiles and profile.name in opponent_profiles
        else None
    )

    return {
        "name": profile.name,
      "displayName": display_name(profile.name),
        "slug": slugify(profile.name),
        "rank": profile.current_rank,
        "score": round(profile.current_score, 3),
        "winRate": round(profile.win_rate, 4),
        "wins": wins,
        "losses": total - wins,
        "avgRank": round(profile.average_rank, 2),
        "pointsPerMatch": round(profile.avg_points_per_match, 3),
        "rawPerformance": round(profile.avg_raw_performance, 3),
        "overperformance": round(profile.avg_overperformance, 3),
        "scoreLost": raw_lost,
        "adjustedScoreLost": adjusted_lost,
        "difficulty": round(difficulty_map.get(profile.name, 0.0), 4) if difficulty_map else 0.0,
        "model": model_path,
        "icon": icon_path,
        "pdf": pdf_path,
        "ranks": ranks,
        "matches": match_points(profile),
        "roundTotals": round_totals,
        "opponent": opp_data,
    }


def attach_character_comparisons(characters: list[dict[str, object]]) -> None:
    by_rank = {int(character["rank"]): character for character in characters}
    for character in characters:
        rank = int(character["rank"])
        comparisons = {
            "rankPlus10": by_rank.get(rank - 10),
            "rankMinus10": by_rank.get(rank + 10),
            "rankPlus5": by_rank.get(rank - 5),
            "rankMinus5": by_rank.get(rank + 5),
        }
        character["comparisons"] = {
            key: {
                "name": value["name"],
                "displayName": value["displayName"],
                "rank": value["rank"],
                "matches": value["matches"],
                "ranks": value["ranks"],
                "roundTotals": value["roundTotals"],
                "icon": value.get("icon"),
            }
            for key, value in comparisons.items()
            if value
        }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_page_data(filename: str, data: dict) -> str:
    """Write page data as window.PAGE_DATA to assets/data/{filename}. Returns site-root-relative path."""
    safe_json = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    write_text(DATA_DIR / filename, f"window.PAGE_DATA={safe_json};")
    return f"assets/data/{filename}"


def page_shell(title: str, body: str, depth: int = 0, data_file: str | None = None, brand_text: str = "Character Analysis and Journey") -> str:
    prefix = "../" * depth
    data_script = f'<script src="{prefix}{data_file}"></script>' if data_file else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{prefix}assets/styles.css">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="{prefix}index.html">{html.escape(brand_text)}</a>
    <nav>
      <a href="{prefix}Smash/index.html">Smash</a>
      <a href="{prefix}assets/profile_pdfs/index.html">PDFs</a>
    </nav>
  </header>
  {body}
  {data_script}
  <script src="{prefix}assets/site.js"></script>
</body>
</html>
"""


CATEGORY_PAGES = [
  ("Gaming", "Gaming", "[+]"),
  ("Economics", "Economics", "Σ$"),
  ("Business", "Business", "∆%"),
  ("Physics", "Physics", "⚛"),
  ("Language", "Language", "Aβ"),
  ("Miscellaneous", "Miscellaneous", "◇"),
]


def home_page() -> str:
    category_links = "\n".join(
        f'<a class="hex-node node-{slug.lower()}" href="{slug}/index.html"><span>{symbol}</span><strong>{label}</strong></a>'
        for slug, label, symbol in CATEGORY_PAGES
    )
    return page_shell(
        "LiamMs_PandasProjects",
        f"""
<main class="home-landing">
  <section class="home-stage">
    <div class="home-copy">
      <h1>Data Analysis</h1>
      <p class="home-signature">By Liam McGrath</p>
    </div>
    <nav class="hex-map" aria-label="Analysis categories">
      <div class="hex-frame" aria-hidden="true"></div>
      {category_links}
    </nav>
  </section>
</main>
""",
        depth=0,
  brand_text="Wonderous Insights Exist Here",
    )


def category_page(label: str) -> str:
    if label == "Gaming":
        return page_shell(
            f"{label} | LiamMs_PandasProjects",
            """
<main class="category-page">
  <section class="category-panel">
    <p class="eyebrow">Gaming analysis</p>
    <h1>Gaming Insights</h1>
    <div class="analysis-directory">
      <article class="game-analysis-card">
        <a class="smash-orb" href="../Smash/index.html" aria-label="Open Super Smash Bros analysis">
          <span class="smash-mark" aria-hidden="true"></span>
        </a>
        <strong>Super Smash Bros</strong>
      </article>
    </div>
  </section>
</main>
""",
            depth=1,
            brand_text="Gaming Insights Exist Here",
        )
    return page_shell(
        f"{label} | LiamMs_PandasProjects",
        """
<main class="placeholder-page">
  <p>To be Filled with Analysis</p>
</main>
""",
        depth=1,
    )


def smash_page(characters: list[dict[str, object]]) -> str:
    total_matches = sum(int(c["wins"]) + int(c["losses"]) for c in characters)
    avg_score = sum(float(c["score"]) for c in characters) / len(characters) if characters else 0
    data_file = _write_page_data("smash.js", {"characters": characters})
    cards = "\n".join(character_tile(c, prefix="../") for c in characters)
    leaders = "\n".join(
      f"<li><span>#{c['rank']}</span><a href=\"{slugify(str(c['name']))}/index.html\">{html.escape(str(c.get('displayName', c['name'])))}</a><strong>{float(c['score']):.2f}</strong></li>"
    for c in characters
    )
    return page_shell(
        "Smash | LiamMs_PandasProjects",
        f"""
<main class="smash-page">
  <section class="smash-hero">
    <div>
      <p class="eyebrow">Smash tournament analytics</p>
      <div class="page-toggle-bar">
        <span class="toggle-pill active">&#9876;&#65039; Fighters</span>
        <a class="toggle-pill" href="Opponents/index.html">&#128737;&#65039; As Opponents</a>
      </div>
      <h1>Smash</h1>
      <p class="lede">Tournament-wide standings, score movement, and fighter profile pages generated from the current pandas records.</p>
    </div>
    <div class="stat-wall">
      <div><strong>{len(characters)}</strong><span>Characters</span></div>
      <div><strong>{total_matches}</strong><span>Recorded matches</span></div>
      <div><strong>{avg_score:.2f}</strong><span>Average score</span></div>
    </div>
  </section>

  <div class="round-selector-bar">
    <p class="eyebrow">View round:</p>
    <div class="round-pills" id="round-pills"></div>
  </div>

  <section class="overview-grid">
    <article class="panel leaderboard-panel">
      <div class="panel-heading">
        <p class="eyebrow">Standings</p>
        <h2>Leaderboard</h2>
      </div>
      <ol class="leader-list" id="smash-leader-list">{leaders}</ol>
    </article>
    <article class="panel chart-panel">
      <div class="panel-heading">
        <p class="eyebrow">Field distribution</p>
        <h2>Score Spread</h2>
      </div>
      <canvas id="overview-chart" width="900" height="360"></canvas>
    </article>
  </section>

  <section class="analysis-links">
    <a class="analysis-card" href="Rank-Atlas/index.html">
      <span>All-character movement</span>
      <strong>Rank Atlas</strong>
    </a>
    <a class="analysis-card" href="Score-Atlas/index.html">
      <span>Total score movement</span>
      <strong>Score Atlas</strong>
    </a>
    <a class="analysis-card" href="Paretos/index.html">
      <span>Every fighter, one KPI at a time</span>
      <strong>KPI Paretos</strong>
    </a>
  </section>

  <section class="select-section">
    <div class="section-title">
      <p class="eyebrow">Character select</p>
      <h2>Choose a Fighter</h2>
    </div>
    <div class="character-grid">{cards}</div>
  </section>
</main>
""",
        depth=1,
        data_file=data_file,
    )


def opponents_page(opponents: list[dict]) -> str:
    total_appearances = sum(int(o.get("appearances", 0) or 0) for o in opponents)
    avg_nt = sum(float(o.get("totalNtScore", 0) or 0) for o in opponents) / len(opponents) if opponents else 0
    data_file = _write_page_data("opponents.js", {"opponents": opponents})
    leaders = "\n".join(
        f'<li><span>#{o["oppRank"]}</span><a href="./{slugify(str(o["name"]))}/index.html">{html.escape(str(o.get("displayName", o["name"])))}</a><strong>{float(o.get("totalNtScore", 0) or 0):.2f}</strong></li>'
        for o in opponents
    )
    cards = "\n".join(opponent_tile(o) for o in opponents)
    return page_shell(
        "Opponents | Smash | LiamMs_PandasProjects",
        f"""
<main class="smash-page">
  <section class="smash-hero">
    <div>
      <p class="eyebrow">Smash tournament analytics</p>
      <div class="page-toggle-bar">
        <a class="toggle-pill" href="../index.html">&#9876;&#65039; Fighters</a>
        <span class="toggle-pill active">&#128737;&#65039; As Opponents</span>
      </div>
      <h1>Opponents</h1>
      <p class="lede">How each fighter performs as the opponent &#8212; ranked by total NT score with no multipliers, no refactoring. Every match calculated identically.</p>
    </div>
    <div class="stat-wall">
      <div><strong>{len(opponents)}</strong><span>Characters</span></div>
      <div><strong>{total_appearances}</strong><span>Total Appearances</span></div>
      <div><strong>{avg_nt:.2f}</strong><span>Avg NT Score</span></div>
    </div>
  </section>

  <section class="overview-grid">
    <article class="panel leaderboard-panel">
      <div class="panel-heading">
        <p class="eyebrow">Ranked by total NT score</p>
        <h2>Opponent Leaderboard</h2>
      </div>
      <ol class="leader-list">{leaders}</ol>
    </article>
    <article class="panel chart-panel">
      <div class="panel-heading">
        <p class="eyebrow">NT score distribution</p>
        <h2>Score Spread</h2>
      </div>
      <canvas id="opp-overview-chart" width="900" height="360"></canvas>
    </article>
  </section>

  <section class="analysis-links" style="margin-top:18px">
    <a class="analysis-card" href="Rank-Atlas/index.html">
      <span>Opponent rank movement</span>
      <strong>Opponent Rank Atlas</strong>
    </a>
  </section>

  <section class="select-section">
    <div class="section-title">
      <p class="eyebrow">View opponent profile</p>
      <h2>Choose a Fighter</h2>
    </div>
    <div class="character-grid">{cards}</div>
  </section>
</main>
""",
        depth=2,
        data_file=data_file,
    )


def opp_rank_atlas_page(opponents: list[dict]) -> str:
    return page_shell(
        "Opponent Rank Atlas | Smash | LiamMs_PandasProjects",
        """
<main class="analysis-page">
  <section class="analysis-hero">
    <div>
      <a class="crumb" href="../index.html">Smash / As Opponents</a>
      <p class="eyebrow">Opponent movement</p>
      <h1>Opponent Rank Atlas</h1>
      <p class="lede">Every character&#8217;s opponent rank trajectory &#8212; ranked by cumulative NT score as opponent at the end of each round.</p>
    </div>
  </section>
  <section class="panel atlas-panel">
    <div class="panel-heading split-heading">
      <div><p class="eyebrow">All opponents</p><h2>Opponent Rank Across Time</h2></div>
      <label class="control-label">Highlights <select id="opp-rank-highlight" multiple size="12"></select></label>
    </div>
    <div class="wide-canvas-wrap"><canvas id="opp-rank-atlas-chart" width="1800" height="980"></canvas></div>
  </section>
</main>
""",
        depth=3,
        data_file=_write_page_data("opp-rank-atlas.js", {"opponents": opponents}),
    )


def rank_atlas_page(characters: list[dict[str, object]]) -> str:
    return page_shell(
        "Rank Atlas | Smash | LiamMs_PandasProjects",
        """
<main class="analysis-page">
  <section class="analysis-hero">
    <div>
      <a class="crumb" href="../index.html">Smash / Analysis</a>
      <p class="eyebrow">Full-field movement</p>
      <h1>Rank Atlas</h1>
      <p class="lede">Every character's tournament rank trajectory on one field. Lower is better; active round boxes are reflected in the rank history.</p>
    </div>
  </section>
  <section class="panel atlas-panel">
    <div class="panel-heading split-heading">
      <div><p class="eyebrow">All characters</p><h2>Rank Across Time</h2></div>
      <label class="control-label">Highlights <select id="rank-highlight" multiple size="12"></select></label>
    </div>
    <div class="wide-canvas-wrap"><canvas id="rank-atlas-chart" width="1800" height="980"></canvas></div>
  </section>
</main>
""",
        depth=2,
        data_file=_write_page_data("rank-atlas.js", {"characters": characters}),
    )


def score_atlas_page(characters: list[dict[str, object]]) -> str:
    return page_shell(
        "Score Atlas | Smash | LiamMs_PandasProjects",
        """
<main class="analysis-page">
  <section class="analysis-hero">
    <div>
      <a class="crumb" href="../index.html">Smash / Analysis</a>
      <p class="eyebrow">Full-field scoring</p>
      <h1>Score Atlas</h1>
      <p class="lede">Every character's total score path across played rounds, with multiselect highlights.</p>
    </div>
  </section>
  <section class="panel atlas-panel">
    <div class="panel-heading split-heading">
      <div><p class="eyebrow">All characters</p><h2>Total Score Across Time</h2></div>
      <label class="control-label">Highlights <select id="score-highlight" multiple size="12"></select></label>
    </div>
    <div class="wide-canvas-wrap"><canvas id="score-atlas-chart" width="1800" height="980"></canvas></div>
  </section>
</main>
""",
        depth=2,
        data_file=_write_page_data("score-atlas.js", {"characters": characters}),
    )


def paretos_page(characters: list[dict[str, object]]) -> str:
    return page_shell(
        "KPI Paretos | Smash | LiamMs_PandasProjects",
        """
<main class="analysis-page">
  <section class="analysis-hero">
    <div>
      <a class="crumb" href="../index.html">Smash / Analysis</a>
      <p class="eyebrow">Field-wide comparisons</p>
      <h1>KPI Paretos</h1>
      <p class="lede">Switch between profile KPIs and see the whole roster ranked on the same chart.</p>
    </div>
  </section>
  <section class="panel pareto-panel">
    <div class="panel-heading split-heading">
      <div><p class="eyebrow">Metric sort</p><h2 id="pareto-title">Pareto</h2></div>
      <label class="control-label">KPI <select id="pareto-metric"></select></label>
    </div>
    <div class="wide-canvas-wrap"><canvas id="pareto-chart" width="1600" height="1280"></canvas></div>
    <div id="pareto-table" class="pareto-table"></div>
  </section>
</main>
""",
        depth=2,
        data_file=_write_page_data("paretos.js", {"characters": characters}),
    )


def pdf_index_page(characters: list[dict[str, object]]) -> str:
    links = "\n".join(
    f'<a class="pdf-row" href="{html.escape(Path(str(character["pdf"])).name)}"><span>#{character["rank"]}</span><strong>{html.escape(str(character.get("displayName", character["name"])))}</strong></a>'
        for character in characters
        if character.get("pdf")
    )
    return page_shell(
        "Profile PDFs | LiamMs_PandasProjects",
        f"""
<main class="analysis-page">
  <section class="analysis-hero">
    <div>
      <a class="crumb" href="../../Smash/index.html">Smash / PDFs</a>
      <p class="eyebrow">Download library</p>
      <h1>Profile PDFs</h1>
      <p class="lede">Generated fighter-card reports for every character with ranking, scoring, and profile visuals.</p>
    </div>
  </section>
  <section class="panel pdf-library">
    {links}
  </section>
</main>
""",
        depth=2,
    )


def character_tile(character: dict[str, object], prefix: str = "") -> str:
    name = str(character["name"])
    shown_name = str(character.get("displayName", name))
    slug = slugify(name)
    icon = character.get("icon")
    model = character.get("model")
    if icon:
        image = f'<img class="tile-icon" src="{prefix}{icon}" alt="" loading="lazy">'
    elif model:
        image = f'<img src="{prefix}{model}" alt="" loading="lazy">'
    else:
      image = f'<span class="initial">{html.escape(shown_name[:1])}</span>'
    return f"""
<a class="fighter-tile" href="{prefix}Smash/{slug}/index.html">
  <div class="tile-art">{image}</div>
  <div class="tile-info">
    <span>#{character['rank']}</span>
    <strong>{html.escape(shown_name)}</strong>
  </div>
</a>"""


def opponent_tile(opp: dict) -> str:
    name = str(opp["name"])
    shown_name = str(opp.get("displayName", name))
    slug = slugify(name)
    icon = opp.get("icon")
    image = f'<img class="tile-icon" src="../../{icon}" alt="" loading="lazy">' if icon else f'<span class="initial">{html.escape(shown_name[:1])}</span>'
    nt = float(opp.get("totalNtScore", 0) or 0)
    return f"""<a class="fighter-tile" href="./{slug}/index.html">
  <div class="tile-art">{image}</div>
  <div class="tile-info">
    <span>#{opp['oppRank']}</span>
    <strong>{html.escape(shown_name)}</strong>
    <em class="opp-nt-label">{nt:.2f} NT</em>
  </div>
</a>"""


def character_page(character: dict[str, object]) -> str:
    shown_name = str(character.get("displayName", character["name"]))
    model = character.get("model")
    icon = character.get("icon")
    pdf = character.get("pdf")
    model_layer = f'<div class="fighter-bg"><img class="fighter-model-img" src="../../{model}" alt="" loading="eager"></div>' if model else ""
    fallback_art = f'<div class="fighter-watermark">{html.escape(shown_name[:1])}</div>' if not model else ""
    icon_html = f'<img class="profile-icon" src="../../{icon}" alt="" loading="lazy">' if icon else f'<span class="profile-icon initial">{html.escape(shown_name[:1])}</span>'
    pdf_link = f'<a class="button ghost" href="../../{pdf}">Open PDF version</a>' if pdf else ""
    kpis = [
        ("Rank", f"#{character['rank']}"),
        ("Total Score", f"{float(character['score']):.2f}"),
        ("Win Rate", f"{float(character['winRate']) * 100:.0f}%"),
        ("Win / Loss", f"{character['wins']} / {character['losses']}"),
        ("Pts / Match", f"{float(character['pointsPerMatch']):.3f}"),
        ("Difficulty", f"{float(character['difficulty']):.2f}"),
        ("Score Lost", f"{float(character['scoreLost']):.3f}"),
        ("Adj Lost", f"{float(character['adjustedScoreLost']):.3f}"),
    ]
    kpi_html = "\n".join(f"<div><span>{label}</span><strong>{value}</strong></div>" for label, value in kpis)
    return page_shell(
        f"{shown_name} | Smash | LiamMs_PandasProjects",
        f"""
<main class="fighter-page fighter-card-page">
  {model_layer}
  {fallback_art}
  <section class="fighter-hero">
    <div class="fighter-copy">
      <a class="crumb" href="../index.html">Smash / Character Select</a>
      <div class="fighter-title-row">{icon_html}<h1>{html.escape(shown_name)}</h1></div>
      <div class="hero-metrics">{kpi_html}</div>
      <div class="profile-actions">{pdf_link}<a class="button primary" href="../index.html">Back to roster</a></div>
    </div>
  </section>

  <section class="profile-chart-grid">
    <article class="panel chart-panel wide"><h2>Score Per Match</h2><canvas id="match-chart" width="1400" height="380"></canvas></article>
    <article class="panel chart-panel wide"><h2>Rank Trajectory</h2><canvas id="rank-chart" width="1400" height="380"></canvas></article>
    <article class="panel chart-panel wide"><h2>Round Score Totals</h2><canvas id="round-chart" width="1400" height="380"></canvas></article>
    <article class="panel chart-panel wide opponent-section"><h2>As Opponent — NT Scores</h2><div class="opp-kpis" id="opp-kpis"></div><canvas id="opp-chart" width="1400" height="380"></canvas></article>
    <article class="panel chart-panel opponent-section"><h2>NT Score by Round</h2><canvas id="opp-round-chart" width="700" height="380"></canvas></article>
    <article class="panel chart-panel opponent-section"><h2>Appearances Log</h2><div id="opp-log" class="opp-log"></div></article>
  </section>
</main>
""",
        depth=2,
        data_file=_write_page_data(f"char/{character['slug']}.js", {"character": character}),
    )


def opponent_character_page(character: dict) -> str:
    shown_name = str(character.get("displayName", character["name"]))
    model = character.get("model")
    icon = character.get("icon")
    opp_rank = character.get("oppRank", "?")
    char_rank = character.get("rank", "?")
    opp = character.get("opponent") or {}
    model_layer = (
        f'<div class="fighter-bg"><img class="fighter-model-img" src="../../../{model}" alt="" loading="eager"></div>'
        if model else ""
    )
    fallback_art = f'<div class="fighter-watermark">{html.escape(shown_name[:1])}</div>' if not model else ""
    icon_html = (
        f'<img class="profile-icon" src="../../../{icon}" alt="" loading="lazy">'
        if icon else f'<span class="profile-icon initial">{html.escape(shown_name[:1])}</span>'
    )
    kpis = [
        ("Opp Rank", f"#{opp_rank}"),
        ("Total NT", f"{float(opp.get('totalNtScore', 0) or 0):.2f}"),
        ("Win Rate", f"{float(opp.get('winRate', 0) or 0) * 100:.0f}%"),
        ("Win / Loss", f"{opp.get('wins', 0)} / {opp.get('losses', 0)}"),
        ("Appearances", str(opp.get("totalAppearances", 0))),
        ("Avg NT", f"{float(opp.get('avgNtScore', 0) or 0):.3f}"),
        ("Fighter Rank", f"#{char_rank}"),
    ]
    kpi_html = "\n".join(f"<div><span>{label}</span><strong>{value}</strong></div>" for label, value in kpis)
    return page_shell(
        f"{shown_name} \u2014 As Opponent | Smash | LiamMs_PandasProjects",
        f"""
<main class="fighter-page fighter-card-page opp-card-page">
  {model_layer}
  {fallback_art}
  <section class="fighter-hero">
    <div class="fighter-copy">
      <a class="crumb" href="../index.html">Smash / Opponents</a>
      <div class="fighter-title-row">{icon_html}<h1>{html.escape(shown_name)}</h1></div>
      <p class="opp-page-badge">&#128737;&#65039; As Opponent &mdash; Rank #{opp_rank}</p>
      <div class="hero-metrics opp-hero-metrics">{kpi_html}</div>
      <div class="profile-actions">
        <a class="button ghost" href="../../{character['slug']}/index.html">View Fighter Profile</a>
        <a class="button primary" href="../index.html">Back to Opponents</a>
      </div>
    </div>
  </section>

  <section class="profile-chart-grid">
    <article class="panel chart-panel wide opponent-section"><h2>NT Score Per Appearance</h2><div class="opp-kpis" id="opp-kpis"></div><canvas id="opp-chart" width="1400" height="380"></canvas></article>
    <article class="panel chart-panel opponent-section"><h2>NT Score by Round</h2><canvas id="opp-round-chart" width="700" height="380"></canvas></article>
    <article class="panel chart-panel opponent-section"><h2>Appearances Log</h2><div id="opp-log" class="opp-log"></div></article>
  </section>
</main>
""",
        depth=3,
        data_file=_write_page_data(f"opp/{character['slug']}.js", {"character": character}),
    )


def write_styles() -> None:
    write_text(
        ASSETS_DIR / "styles.css",
        """
:root {
  --bg: #08111f;
  --panel: rgba(17, 28, 47, 0.82);
  --panel-strong: #121f34;
  --line: #263955;
  --text: #e8edf6;
  --muted: #8ea3bf;
  --cyan: #00c8ff;
  --gold: #ffd369;
  --green: #4ade80;
  --red: #f87171;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  background:
    linear-gradient(115deg, rgba(118,42,210,.34), transparent 34%),
    repeating-linear-gradient(60deg, rgba(255,255,255,.045) 0 1px, transparent 1px 34px),
    radial-gradient(ellipse at 50% 0%, rgba(196,83,255,.42), transparent 56%),
    linear-gradient(135deg, #170a30, #32125f 48%, #11081f);
  color: var(--text);
  min-height: 100vh;
}
a { color: inherit; text-decoration: none; }
.site-header {
  position: sticky; top: 0; z-index: 10;
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 28px;
  background: rgba(8,17,31,.78); backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--line);
}
.brand { font-weight: 800; letter-spacing: .02em; }
.site-header nav { display: flex; gap: 18px; color: var(--muted); font-size: 14px; }
.home-hero, .smash-page, .analysis-page { width: min(1320px, calc(100% - 36px)); margin: 0 auto; }
.fighter-page { width: min(1480px, calc(100% - 36px)); margin: 0 auto; }
.home-landing { min-height: calc(100vh - 65px); display: grid; place-items: center; overflow: hidden; }
.home-stage { width: min(1360px, calc(100% - 36px)); min-height: 720px; display: grid; grid-template-columns: .7fr 1.3fr; gap: 42px; align-items: center; }
.home-copy { position: relative; z-index: 1; }
.home-copy h1 { max-width: 620px; font-size: clamp(62px, 9vw, 132px); line-height: .86; letter-spacing: 0; text-wrap: balance; }
.home-signature { margin: 24px 0 0; font-family: "Palatino Linotype", "Book Antiqua", Palatino, serif; font-size: clamp(24px, 3vw, 46px); font-style: italic; color: #e9d7ff; }
.hex-map { position: relative; width: min(760px, 96vw); aspect-ratio: 1; margin: 0 auto; }
.hex-frame { position: absolute; inset: 8%; clip-path: polygon(50% 0, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%); background: linear-gradient(135deg, rgba(210,154,255,.26), rgba(82,18,156,.32)); border: 1px solid rgba(238,218,255,.4); box-shadow: inset 0 0 90px rgba(250,225,255,.18), 0 34px 120px rgba(19,6,44,.52); }
.hex-frame::after { content: ""; position: absolute; inset: 9%; clip-path: inherit; border: 1px solid rgba(255,255,255,.26); background: repeating-linear-gradient(120deg, rgba(255,255,255,.08) 0 1px, transparent 1px 22px); }
.hex-node { position: absolute; width: 172px; min-height: 150px; display: grid; place-items: center; align-content: center; gap: 10px; padding: 16px; clip-path: polygon(50% 0, 95% 25%, 95% 75%, 50% 100%, 5% 75%, 5% 25%); background: linear-gradient(160deg, rgba(31,12,63,.96), rgba(17,6,36,.88)); border: 1px solid rgba(238,218,255,.42); text-align: center; box-shadow: 0 22px 52px rgba(0,0,0,.36), inset 0 0 34px rgba(213,154,255,.12); }
.hex-node span { display: grid; place-items: center; width: 66px; height: 66px; border-radius: 50%; background: radial-gradient(circle, rgba(218,166,255,.42), rgba(93,31,151,.26)); color: #f1dcff; font-family: Georgia, serif; font-size: 32px; font-weight: 900; box-shadow: inset 0 0 18px rgba(255,255,255,.08); }
.hex-node strong { font-size: 16px; color: #f8efff; }
.node-gaming { left: 50%; top: 2%; transform: translateX(-50%); }
.node-economics { right: 5%; top: 24%; }
.node-business { right: 5%; bottom: 24%; }
.node-physics { left: 50%; bottom: 2%; transform: translateX(-50%); }
.node-language { left: 5%; bottom: 24%; }
.node-miscellaneous { left: 5%; top: 24%; }
.placeholder-page { min-height: calc(100vh - 65px); display: grid; place-items: center; }
.placeholder-page p { margin: 0; font-size: clamp(28px, 5vw, 68px); font-weight: 900; text-align: center; color: #f2e7ff; }
.category-page { width: min(1180px, calc(100% - 36px)); min-height: calc(100vh - 65px); margin: 0 auto; display: grid; align-items: center; justify-items: center; padding: 54px 0; }
.category-panel { width: min(760px, 100%); text-align: center; }
.category-panel h1 { font-size: clamp(48px, 7vw, 96px); }
.analysis-directory { margin-top: 34px; display: grid; justify-content: center; gap: 18px; }
.game-analysis-card { width: min(380px, calc(100vw - 54px)); min-height: 316px; display: grid; place-items: center; align-content: center; gap: 20px; padding: 30px; border: 1px solid rgba(238,218,255,.34); border-radius: 8px; background: linear-gradient(155deg, rgba(20,7,42,.86), rgba(15,5,32,.72)); box-shadow: 0 26px 78px rgba(16,5,38,.36), inset 0 0 36px rgba(255,255,255,.04); }
.game-analysis-card strong { font-size: 30px; color: #f4ecff; text-align: center; text-shadow: 0 3px 0 rgba(0,0,0,.34); }
.smash-orb { width: 178px; height: 178px; border-radius: 50%; clip-path: circle(50%); display: grid; place-items: center; cursor: pointer; transition: transform .18s ease, filter .18s ease; }
.smash-orb:hover { transform: translateY(-4px) scale(1.03); filter: drop-shadow(0 20px 28px rgba(0,0,0,.34)); }
.smash-mark { position: relative; width: 164px; height: 164px; border-radius: 50%; background: #f8f3ff; box-shadow: 0 0 0 12px rgba(255,255,255,.08), 0 18px 44px rgba(0,0,0,.34); overflow: hidden; }
.smash-mark::before { content: ""; position: absolute; left: 44%; top: 0; width: 12%; height: 100%; background: #130b24; }
.smash-mark::after { content: ""; position: absolute; left: 0; top: 47%; width: 100%; height: 10%; background: #130b24; }
.home-panel, .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 20px 80px rgba(0,0,0,.32); }
.home-panel { padding: 48px; width: min(760px, 100%); }
.eyebrow { margin: 0 0 10px; color: var(--cyan); text-transform: uppercase; font-size: 12px; letter-spacing: .14em; font-weight: 800; }
h1, h2 { margin: 0; line-height: 1; }
h1 { font-size: clamp(48px, 8vw, 96px); }
h2 { font-size: 28px; }
.lede { color: var(--muted); font-size: 18px; line-height: 1.55; max-width: 760px; }
.button { display: inline-flex; align-items: center; justify-content: center; min-height: 42px; padding: 0 18px; border-radius: 6px; border: 1px solid var(--line); font-weight: 800; }
.button.primary { background: var(--cyan); color: #06101b; border-color: transparent; }
.button.ghost { color: var(--text); background: rgba(255,255,255,.04); }
.home-actions, .profile-actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 24px; }
.smash-hero, .fighter-hero { display: grid; grid-template-columns: 1.4fr .9fr; gap: 24px; align-items: stretch; padding: 42px 0 26px; }
.fighter-card-page { position: relative; min-height: calc(100vh - 65px); isolation: isolate; }
.fighter-card-page::before { content: ""; position: fixed; inset: 65px 0 0; z-index: -3; background: linear-gradient(90deg, rgba(8,17,31,.99) 0%, rgba(8,17,31,.96) 44%, rgba(8,17,31,.62) 68%, rgba(8,17,31,.28) 100%); pointer-events: none; }
.fighter-card-page::after { content: ""; position: fixed; inset: 65px 0 0; z-index: -2; background: repeating-linear-gradient(135deg, rgba(255,255,255,.045) 0 1px, transparent 1px 12px); opacity: .28; pointer-events: none; }
.fighter-bg { position: fixed; inset: 65px 0 0; z-index: -4; pointer-events: none; display: flex; align-items: flex-end; justify-content: flex-end; overflow: hidden; }
.fighter-model-img { flex: 0 0 auto; height: min(100vh, 1100px); width: auto; max-width: min(92vw, 1800px); object-fit: contain; object-position: right bottom; opacity: .70; filter: drop-shadow(-28px -6px 44px rgba(0,0,0,.56)) saturate(1.12) contrast(1.05); }
.fighter-watermark { position: fixed; right: 10vw; top: 20vh; z-index: -4; font-size: min(40vw, 540px); font-weight: 900; color: rgba(232,237,246,.08); pointer-events: none; }
.stat-wall { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.stat-wall div, .hero-metrics div { background: rgba(18,31,52,.74); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }
.stat-wall strong, .hero-metrics strong { display: block; font-size: 28px; color: var(--gold); }
.stat-wall span, .hero-metrics span { color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 800; }
.overview-grid { display: grid; grid-template-columns: minmax(380px, .78fr) minmax(640px, 1.42fr); gap: 18px; align-items: stretch; }
.leaderboard-panel { max-height: 460px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(0,200,255,.55) rgba(8,17,31,.42); }
.overview-grid .chart-panel { min-height: 420px; overflow: visible; }
.leaderboard-panel::-webkit-scrollbar { width: 10px; }
.leaderboard-panel::-webkit-scrollbar-thumb { background: rgba(0,200,255,.55); border-radius: 999px; }
.leaderboard-panel::-webkit-scrollbar-track { background: rgba(8,17,31,.42); }
.round-selector-bar { display: flex; align-items: center; gap: 14px; margin: 6px 0 18px; flex-wrap: wrap; }
.round-selector-bar .eyebrow { margin: 0; white-space: nowrap; }
.round-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.round-pill { padding: 7px 16px; border-radius: 6px; border: 1px solid var(--line); background: rgba(18,31,52,.74); color: var(--muted); font: inherit; font-size: 13px; font-weight: 800; cursor: pointer; transition: background .14s, color .14s; }
.round-pill:hover { background: rgba(18,31,52,1); color: var(--text); }
.round-pill.active { background: var(--cyan); color: #06101b; border-color: transparent; }
.analysis-links { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 18px 0 6px; }
.analysis-card { display: block; padding: 22px; background: rgba(18,31,52,.76); border: 1px solid var(--line); border-radius: 8px; }
.analysis-card span { display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 800; letter-spacing: .12em; }
.analysis-card strong { display: block; margin-top: 8px; font-size: 30px; color: var(--text); }
.panel { padding: 20px; }
.leader-list { list-style: none; padding: 0; margin: 18px 0 0; display: grid; gap: 10px; }
.leader-list li { display: grid; grid-template-columns: 44px 1fr auto; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(142,163,191,.18); }
.leader-list span { color: var(--gold); font-weight: 800; }
.select-section { padding: 32px 0 56px; }
.section-title { margin-bottom: 18px; }
.character-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(145px, 1fr)); gap: 12px; }
.fighter-tile { position: relative; min-height: 190px; overflow: hidden; background: #101b2d; border: 1px solid var(--line); border-radius: 8px; }
.tile-art { position: absolute; inset: 0; display: grid; place-items: center; background: linear-gradient(150deg, rgba(0,200,255,.15), rgba(255,211,105,.10)); }
.tile-art img { width: 130%; height: 130%; object-fit: cover; opacity: .72; transform: translateY(-3%); }
.tile-art img.tile-icon { width: 92px; height: 92px; object-fit: contain; opacity: 1; transform: none; filter: drop-shadow(0 10px 14px rgba(0,0,0,.45)); }
.initial, .profile-initial { font-size: 76px; font-weight: 900; color: rgba(232,237,246,.28); }
.tile-info { position: absolute; inset: auto 0 0; padding: 42px 12px 12px; background: linear-gradient(transparent, rgba(8,17,31,.96)); }
.tile-info span { color: var(--gold); font-weight: 900; }
.tile-info strong { display: block; font-size: 17px; }
.fighter-hero { min-height: 330px; grid-template-columns: minmax(520px, 880px) 1fr; padding: 46px 0 24px; }
.fighter-copy { padding: 22px 0; }
.fighter-copy h1 { max-width: 680px; font-size: clamp(58px, 7vw, 112px); line-height: .9; text-shadow: 0 4px 0 rgba(0,0,0,.45); }
.fighter-title-row { display: flex; align-items: center; gap: 22px; }
.profile-icon { flex: 0 0 auto; width: 118px; height: 118px; object-fit: contain; border-radius: 50%; background: rgba(8,17,31,.58); border: 1px solid rgba(238,218,255,.32); box-shadow: 0 18px 42px rgba(0,0,0,.34); }
.profile-icon.initial { display: grid; place-items: center; font-size: 58px; }
.crumb { color: var(--muted); font-size: 13px; }
.hero-metrics { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; margin-top: 26px; max-width: 740px; }
.fighter-card-page .hero-metrics div { background: rgba(18,31,52,.84); }
.fighter-art { position: relative; overflow: hidden; border-radius: 8px; border: 1px solid var(--line); background: rgba(18,31,52,.65); min-height: 360px; display: grid; place-items: center; }
.profile-model { width: 100%; height: 100%; object-fit: cover; opacity: .86; }
.profile-chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; padding-bottom: 56px; max-width: 1380px; }
.fighter-card-page .chart-panel { background: rgba(17,28,47,.88); backdrop-filter: blur(6px); }
.profile-chart-grid .wide { grid-column: 1 / -1; }
.profile-chart-grid .chart-panel { overflow-x: visible; }
.profile-chart-grid canvas { min-width: unset; }
.profile-chart-grid .wide canvas { min-width: unset; }
.opponent-section h2 { color: #c084fc; }
.opp-kpis { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.opp-kpi { background: rgba(18,31,52,.74); border: 1px solid rgba(192,132,252,.28); border-radius: 8px; padding: 12px 18px; }
.opp-kpi strong { display: block; font-size: 22px; color: #c084fc; }
.opp-kpi span { font-size: 11px; color: var(--muted); text-transform: uppercase; font-weight: 800; letter-spacing: .1em; }
.opp-log { display: grid; gap: 6px; max-height: 360px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(192,132,252,.45) rgba(8,17,31,.42); }
.opp-row { display: grid; grid-template-columns: 72px 28px 1fr auto; gap: 8px; align-items: center; padding: 7px 10px; background: rgba(8,17,31,.42); border: 1px solid rgba(142,163,191,.14); border-radius: 6px; font-size: 13px; }
.opp-row .opp-round { color: var(--muted); font-size: 11px; }
.opp-row .opp-win { color: #4ade80; font-weight: 900; }
.opp-row .opp-loss { color: #f87171; font-weight: 900; }
.opp-row .opp-nt { color: #c084fc; font-weight: 800; }
.analysis-hero { padding: 42px 0 26px; }
.atlas-panel, .pareto-panel { margin-bottom: 56px; }
.split-heading { display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 16px; }
.control-label { display: grid; gap: 6px; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 800; letter-spacing: .08em; }
select { min-width: 220px; min-height: 38px; border: 1px solid var(--line); border-radius: 6px; background: #101b2d; color: var(--text); padding: 0 12px; font: inherit; }
select[multiple] { min-width: 250px; min-height: 240px; padding: 8px 0; }
select[multiple] option { padding: 6px 14px; }
.wide-canvas-wrap { width: 100%; overflow-x: auto; border-radius: 8px; }
.wide-canvas-wrap canvas { min-width: 1100px; }
.pareto-table { margin-top: 16px; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px; }
.pareto-row { display: grid; grid-template-columns: 42px 1fr auto; gap: 10px; align-items: center; padding: 9px 10px; background: rgba(8,17,31,.42); border: 1px solid rgba(142,163,191,.16); border-radius: 6px; }
.pareto-row span { color: var(--gold); font-weight: 900; }
.pareto-row a { color: var(--text); }
.pareto-row strong { color: var(--cyan); }
.pdf-library { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 10px; margin-bottom: 56px; }
.pdf-row { display: grid; grid-template-columns: 44px 1fr; gap: 10px; align-items: center; min-height: 52px; padding: 12px; background: rgba(8,17,31,.42); border: 1px solid rgba(142,163,191,.16); border-radius: 6px; }
.pdf-row span { color: var(--gold); font-weight: 900; }
.pdf-row strong { color: var(--text); }
canvas { width: 100%; height: auto; display: block; }
.page-toggle-bar { display: inline-flex; gap: 0; margin-bottom: 30px; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
.toggle-pill { display: inline-flex; align-items: center; gap: 8px; padding: 16px 38px; font-size: 20px; font-weight: 900; letter-spacing: .03em; }
.toggle-pill.active { background: var(--cyan); color: #06101b; }
.toggle-pill:not(.active) { background: rgba(18,31,52,.74); color: var(--muted); transition: background .14s, color .14s; }
.toggle-pill:not(.active):hover { background: rgba(18,31,52,.95); color: var(--text); }
.panel-heading { margin-bottom: 0; }
.opp-nt-label { display: block; font-size: 13px; color: #c084fc; font-weight: 800; margin-top: 3px; font-style: normal; }
.opp-page-badge { margin: 6px 0 18px; font-size: 18px; font-weight: 900; color: #c084fc; letter-spacing: .04em; }
.opp-hero-metrics strong { color: #c084fc; }
.opp-card-page .fighter-card-page::before { background: linear-gradient(90deg, rgba(8,6,28,.99) 0%, rgba(8,6,28,.96) 44%, rgba(8,6,28,.62) 68%, rgba(8,6,28,.28) 100%); }
@media (max-width: 820px) {
  .smash-hero, .fighter-hero, .overview-grid, .profile-chart-grid, .analysis-links { grid-template-columns: 1fr; }
  .home-stage { grid-template-columns: 1fr; min-height: auto; padding: 44px 0; }
  .hex-node { width: 112px; min-height: 98px; }
  .hex-node span { width: 44px; height: 44px; font-size: 22px; }
  .hex-node strong { font-size: 12px; }
  .stat-wall, .hero-metrics { grid-template-columns: 1fr 1fr; }
  .split-heading { align-items: start; flex-direction: column; }
  h1 { font-size: 48px; }
}
""".strip(),
    )


def write_script() -> None:
    write_text(
        ASSETS_DIR / "site.js",
        """
function pageData() {
  return window.PAGE_DATA || {};
}
function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function drawAxes(ctx, width, height, pad, opts = {}) {
  ctx.strokeStyle = '#263955';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad.l, pad.t); ctx.lineTo(pad.l, height - pad.b); ctx.lineTo(width - pad.r, height - pad.b); ctx.stroke();
  const lines = opts.lines || 4;
  const max = opts.max || 0;
  ctx.fillStyle = '#8ea3bf';
  ctx.font = '12px Georgia';
  for (let i = 0; i <= lines; i++) {
    const y = pad.t + (height - pad.t - pad.b) * i / lines;
    ctx.strokeStyle = 'rgba(255,255,255,.09)';
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(width - pad.r, y); ctx.stroke();
    if (opts.values) {
      const value = max - (max * i / lines);
      ctx.fillStyle = '#8ea3bf';
      ctx.textAlign = 'right';
      ctx.fillText(value.toFixed(max >= 10 ? 0 : 1), pad.l - 10, y + 4);
      ctx.textAlign = 'left';
    }
  }
}
function drawBarChart(canvas, labels, series, title, yLabel, opts = {}) {
  if (!canvas || !labels.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const line = opts.line || null;
  const pad = {l: 58, r: line ? 70 : 24, t: 30, b: 72};
  const max = Math.max(1, ...series.flatMap(s => s.values.map(v => Math.max(0, v))));
  drawAxes(ctx, width, height, pad, {values: true, max});
  const plotW = width - pad.l - pad.r;
  const plotH = height - pad.t - pad.b;
  const cluster = plotW / labels.length;
  const barW = Math.min(34, cluster / (series.length + 1));
  series.forEach((s, si) => {
    ctx.fillStyle = s.color;
    s.values.forEach((v, i) => {
      const x = pad.l + i * cluster + cluster / 2 + (si - (series.length - 1) / 2) * barW;
      const h = Math.max(1, (v / max) * plotH);
      ctx.globalAlpha = s.alpha || 1;
      ctx.fillRect(x - barW * .42, height - pad.b - h, barW * .84, h);
      ctx.globalAlpha = 1;
    });
  });
  if (line && (line.values || []).length) {
    const lineMax = Math.max(1, ...line.values.map(v => Math.max(0, Number(v) || 0)));
    const xAt = i => pad.l + i * cluster + cluster / 2;
    const yAt = v => pad.t + (1 - (Number(v) || 0) / lineMax) * plotH;
    ctx.strokeStyle = line.color || css('--gold');
    ctx.lineWidth = 3;
    ctx.beginPath();
    line.values.forEach((v, i) => { const x = xAt(i), y = yAt(v); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke();
    line.values.forEach((v, i) => {
      const x = xAt(i), y = yAt(v);
      ctx.fillStyle = line.color || css('--gold'); ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 10px Georgia'; ctx.textAlign = 'center'; ctx.fillText(Number(v).toFixed(1), x, y - 8); ctx.textAlign = 'left';
    });
    ctx.fillStyle = '#8ea3bf'; ctx.font = '12px Georgia';
    for (let i = 0; i <= 5; i++) {
      const value = lineMax - (lineMax * i / 5);
      const y = pad.t + plotH * i / 5;
      ctx.fillText(value.toFixed(lineMax >= 10 ? 0 : 1), width - pad.r + 8, y + 4);
    }
    ctx.save(); ctx.translate(width - 18, height / 2); ctx.rotate(Math.PI / 2); ctx.fillText(line.label || 'Total Score', 0, 0); ctx.restore();
  }
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 16px Georgia'; ctx.fillText(title, pad.l, 20);
  ctx.fillStyle = '#8ea3bf'; ctx.font = '12px Georgia';
  labels.forEach((label, i) => {
    const x = pad.l + i * cluster + cluster / 2;
    ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.55); ctx.textAlign = 'right'; ctx.fillText(label, 0, 0); ctx.restore();
  });
  ctx.save(); ctx.translate(16, height / 2); ctx.rotate(-Math.PI / 2); ctx.fillText(yLabel, 0, 0); ctx.restore();
  if (!opts.hideLegend) {
    let lx = pad.l, ly = 34;
    series.forEach(s => { ctx.fillStyle = s.color; ctx.fillRect(lx, ly, 12, 8); ctx.fillStyle = '#e8edf6'; ctx.fillText(s.name, lx + 18, ly + 8); lx += ctx.measureText(s.name).width + 48; });
    if (line) { ctx.strokeStyle = line.color || css('--gold'); ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(lx, ly + 4); ctx.lineTo(lx + 18, ly + 4); ctx.stroke(); ctx.fillStyle = '#e8edf6'; ctx.fillText(line.name || line.label || 'Total Score', lx + 24, ly + 8); }
  }
}
function matchValueMap(matches) {
  const map = new Map();
  (matches || []).forEach(m => map.set(`${m.round} M${m.match}`, Number(m.score) || 0));
  return map;
}
function drawCustomBarChart(canvas, labels, values, colors, title, yLabel) {
  if (!canvas || !labels.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const pad = {l: 58, r: 24, t: 30, b: 72};
  const max = Math.max(0.01, ...values.map(v => Math.abs(v)));
  drawAxes(ctx, width, height, pad, {values: true, max});
  const plotW = width - pad.l - pad.r;
  const plotH = height - pad.t - pad.b;
  const barW = Math.max(8, plotW / labels.length * 0.65);
  values.forEach((v, i) => {
    const x = pad.l + i * (plotW / labels.length) + (plotW / labels.length) / 2;
    const h = Math.max(1, (Math.abs(v) / max) * plotH);
    ctx.fillStyle = colors[i] || '#c084fc';
    ctx.globalAlpha = 0.85;
    ctx.fillRect(x - barW / 2, height - pad.b - h, barW, h);
    ctx.globalAlpha = 1;
    if (Math.abs(v) > 0.01) {
      ctx.fillStyle = '#e8edf6'; ctx.font = '9px Georgia'; ctx.textAlign = 'center';
      ctx.fillText(v.toFixed(2), x, height - pad.b - h - 4);
      ctx.textAlign = 'left';
    }
  });
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 16px Georgia'; ctx.fillText(title, pad.l, 20);
  ctx.fillStyle = '#8ea3bf'; ctx.font = '11px Georgia';
  labels.forEach((label, i) => {
    const x = pad.l + i * (plotW / labels.length) + (plotW / labels.length) / 2;
    ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.55); ctx.textAlign = 'right'; ctx.fillText(label, 0, 0); ctx.restore();
  });
  ctx.save(); ctx.translate(16, height / 2); ctx.rotate(-Math.PI / 2); ctx.fillText(yLabel, 0, 0); ctx.restore();
}
function roundValueMap(roundTotals) {
  const map = new Map();
  (roundTotals || []).forEach(r => map.set(r.round, Number(r.score) || 0));
  return map;
}
function ranksByRoundMap(ranks) {
  const map = new Map();
  (ranks || []).forEach(r => map.set(r.roundLabel, r));
  return map;
}
function comparisonSeries(character) {
  const c = character.comparisons || {};
  return [
    c.rankPlus10 && {character: c.rankPlus10, color: '#ffd369', label: '+10 rank'},
    c.rankMinus10 && {character: c.rankMinus10, color: '#f87171', label: '-10 rank'},
    c.rankPlus5 && {character: c.rankPlus5, color: '#d6b04d', label: '+5 rank'},
    c.rankMinus5 && {character: c.rankMinus5, color: '#b85866', label: '-5 rank'}
  ].filter(Boolean);
}
function drawRankComparisonChart(canvas, character, title) {
  if (!canvas || !(character.ranks || []).length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const pad = {l: 58, r: 24, t: 30, b: 72};
  const labels = character.ranks.map(p => p.roundLabel);
  const displayLabels = character.ranks.map(p => p.round);
  const allRanks = [character, ...comparisonSeries(character).map(s => s.character)].flatMap(c => (c.ranks || []).map(p => p.rank));
  const min = Math.max(1, Math.min(...allRanks) - 2), max = Math.min(86, Math.max(...allRanks) + 2);
  drawAxes(ctx, width, height, pad, {lines: 6});
  const xAt = i => pad.l + (width - pad.l - pad.r) * (labels.length === 1 ? .5 : i / (labels.length - 1));
  const yAt = r => pad.t + (r - min) / (max - min || 1) * (height - pad.t - pad.b);
  const drawSeries = (series, color, widthLine, alpha, dash = []) => {
    const rankMap = ranksByRoundMap(series.ranks);
    ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = widthLine; ctx.globalAlpha = alpha; ctx.setLineDash(dash); ctx.beginPath();
    let started = false;
    labels.forEach((label, i) => {
      if (!rankMap.has(label)) return;
      const x = xAt(i), y = yAt(rankMap.get(label).rank);
      started ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      started = true;
    });
    ctx.stroke(); ctx.restore();
  };
  comparisonSeries(character).forEach((series, index) => drawSeries(series.character, series.color, 2, .7, index < 2 ? [7, 5] : [2, 4]));
  drawSeries(character, css('--cyan'), 4, 1);
  const own = ranksByRoundMap(character.ranks);
  labels.forEach((label, i) => {
    if (!own.has(label)) return;
    const x = xAt(i), y = yAt(own.get(label).rank);
    ctx.fillStyle = css('--cyan'); ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 12px Georgia'; ctx.fillText(own.get(label).rank, x - 8, y - 11);
  });
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 16px Georgia'; ctx.fillText(title, pad.l, 20);
  ctx.fillStyle = '#8ea3bf'; ctx.font = '12px Georgia';
  displayLabels.forEach((label, i) => { const x = xAt(i); ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.55); ctx.textAlign = 'right'; ctx.fillText(label, 0, 0); ctx.restore(); });
  ctx.save(); ctx.translate(16, height / 2); ctx.rotate(-Math.PI / 2); ctx.fillText('Rank (lower = better)', 0, 0); ctx.restore();
}
function drawLineChart(canvas, points, title) {
  if (!canvas || !points.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const pad = {l: 58, r: 24, t: 30, b: 72};
  const ranks = points.map(p => p.rank);
  const min = Math.min(...ranks) - 2, max = Math.max(...ranks) + 2;
  drawAxes(ctx, width, height, pad);
  const xAt = i => pad.l + (width - pad.l - pad.r) * (points.length === 1 ? .5 : i / (points.length - 1));
  const yAt = r => pad.t + (r - min) / (max - min || 1) * (height - pad.t - pad.b);
  ctx.strokeStyle = css('--cyan'); ctx.lineWidth = 4; ctx.beginPath();
  points.forEach((p, i) => { const x = xAt(i), y = yAt(p.rank); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
  ctx.stroke();
  points.forEach((p, i) => { const x = xAt(i), y = yAt(p.rank); ctx.fillStyle = css('--cyan'); ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 12px Georgia'; ctx.fillText(p.rank, x - 8, y - 11); });
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 16px Georgia'; ctx.fillText(title, pad.l, 20);
  ctx.fillStyle = '#8ea3bf'; ctx.font = '12px Georgia';
  points.forEach((p, i) => { const x = xAt(i); ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.55); ctx.textAlign = 'right'; ctx.fillText(p.round, 0, 0); ctx.restore(); });
}
const ROUND_ORDER = {round_1:1, round_2:2, elimination_1:3, round_3:4, elimination_2:5, round_4:6, elimination_3:7, round_5:8, elimination_4:9, round_6:10};
function allRounds(chars) {
  const seen = new Map();
  chars.forEach(c => (c.ranks || []).forEach(p => { if (!seen.has(p.roundLabel)) seen.set(p.roundLabel, p.round); }));
  return Array.from(seen, ([roundLabel, round]) => ({roundLabel, round}))
    .sort((a, b) => (ROUND_ORDER[a.roundLabel] || 99) - (ROUND_ORDER[b.roundLabel] || 99));
}
function drawRankAtlas(canvas, chars, highlightNames) {
  if (!canvas || !chars.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const highlightSet = new Set(highlightNames || []);
  const pad = {l: 70, r: 190, t: 40, b: 82};
  const rounds = allRounds(chars);
  const xAt = i => pad.l + (width - pad.l - pad.r) * (rounds.length === 1 ? .5 : i / (rounds.length - 1));
  const yAt = rank => pad.t + (rank - 1) / 85 * (height - pad.t - pad.b);
  drawAxes(ctx, width, height, pad, {lines: 8});
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 18px Georgia'; ctx.fillText('Every Character Rank Trajectory', pad.l, 24);
  rounds.forEach((r, i) => { const x = xAt(i); ctx.fillStyle = '#8ea3bf'; ctx.font = '13px Georgia'; ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.45); ctx.textAlign = 'right'; ctx.fillText(r.round, 0, 0); ctx.restore(); });
  const colors = ['#00c8ff', '#ffd369', '#4ade80', '#f87171', '#b07aa1', '#76b7b2', '#edc948', '#e15759'];
  const highlightColors = ['#00c8ff', '#ffd369', '#4ade80', '#f87171', '#f0abfc', '#38bdf8', '#fb923c', '#c4b5fd'];
  let highlightIndex = 0;
  chars.forEach((c, ci) => {
    const map = new Map((c.ranks || []).map(p => [p.roundLabel, p.rank]));
    const isHi = highlightSet.has(c.name);
    const hiColor = highlightColors[highlightIndex % highlightColors.length];
    if (isHi) highlightIndex += 1;
    ctx.strokeStyle = isHi ? hiColor : colors[ci % colors.length];
    ctx.globalAlpha = isHi ? 1 : 0.16;
    ctx.lineWidth = isHi ? 4 : 1.2;
    ctx.beginPath();
    let started = false;
    rounds.forEach((r, i) => {
      if (!map.has(r.roundLabel)) return;
      const x = xAt(i), y = yAt(map.get(r.roundLabel));
      started ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      started = true;
    });
    ctx.stroke();
    ctx.globalAlpha = 1;
    if (isHi) {
      rounds.forEach((r, i) => {
        if (!map.has(r.roundLabel)) return;
        const x = xAt(i), y = yAt(map.get(r.roundLabel));
        ctx.fillStyle = hiColor; ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 12px Georgia'; ctx.fillText(map.get(r.roundLabel), x + 8, y - 8);
      });
      const last = c.ranks[c.ranks.length - 1];
      ctx.fillStyle = hiColor; ctx.font = 'bold 15px Georgia'; ctx.fillText(`${c.name} #${last.rank}`, width - pad.r + 20, yAt(last.rank) + 5);
    }
  });
}
function drawScoreAtlas(canvas, chars, highlightNames) {
  if (!canvas || !chars.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const highlightSet = new Set(highlightNames || []);
  const pad = {l: 76, r: 210, t: 40, b: 82};
  const rounds = allRounds(chars);
  const allScores = chars.flatMap(c => (c.matches || []).map(m => Number(m.accumulatedScore) || 0));
  const max = Math.max(1, ...allScores);
  const xAt = i => pad.l + (width - pad.l - pad.r) * (rounds.length === 1 ? .5 : i / (rounds.length - 1));
  const yAt = score => pad.t + (1 - score / max) * (height - pad.t - pad.b);
  drawAxes(ctx, width, height, pad, {values: true, max, lines: 8});
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 18px Georgia'; ctx.fillText('Every Character Total Score Trajectory', pad.l, 24);
  rounds.forEach((r, i) => { const x = xAt(i); ctx.fillStyle = '#8ea3bf'; ctx.font = '13px Georgia'; ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.45); ctx.textAlign = 'right'; ctx.fillText(r.round, 0, 0); ctx.restore(); });
  const colors = ['#00c8ff', '#ffd369', '#4ade80', '#f87171', '#b07aa1', '#76b7b2', '#edc948', '#e15759'];
  const highlightColors = ['#00c8ff', '#ffd369', '#4ade80', '#f87171', '#f0abfc', '#38bdf8', '#fb923c', '#c4b5fd'];
  let highlightIndex = 0;
  chars.forEach((c, ci) => {
    const map = new Map();
    (c.matches || []).forEach(m => map.set(m.roundLabel, Number(m.accumulatedScore) || 0));
    const isHi = highlightSet.has(c.name);
    const hiColor = highlightColors[highlightIndex % highlightColors.length];
    if (isHi) highlightIndex += 1;
    ctx.strokeStyle = isHi ? hiColor : colors[ci % colors.length];
    ctx.globalAlpha = isHi ? 1 : 0.14;
    ctx.lineWidth = isHi ? 4 : 1.2;
    ctx.beginPath();
    let started = false;
    rounds.forEach((r, i) => {
      if (!map.has(r.roundLabel)) return;
      const x = xAt(i), y = yAt(map.get(r.roundLabel));
      started ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      started = true;
    });
    ctx.stroke();
    ctx.globalAlpha = 1;
    if (isHi) {
      let lastScore = null;
      rounds.forEach((r, i) => {
        if (!map.has(r.roundLabel)) return;
        const score = map.get(r.roundLabel);
        const x = xAt(i), y = yAt(score);
        lastScore = score;
        ctx.fillStyle = hiColor; ctx.beginPath(); ctx.arc(x, y, 6, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 12px Georgia'; ctx.fillText(score.toFixed(1), x + 8, y - 8);
      });
      if (lastScore !== null) { ctx.fillStyle = hiColor; ctx.font = 'bold 15px Georgia'; ctx.fillText(`${c.name} ${lastScore.toFixed(1)}`, width - pad.r + 20, yAt(lastScore) + 5); }
    }
  });
}
function drawOppRankAtlas(canvas, opps, highlightNames) {
  if (!canvas || !opps.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const highlightSet = new Set(highlightNames || []);
  const pad = {l: 70, r: 190, t: 40, b: 82};
  const seen = new Map();
  opps.forEach(o => (o.oppRanks || []).forEach(p => { if (!seen.has(p.roundLabel)) seen.set(p.roundLabel, p.round); }));
  const rounds = Array.from(seen, ([rl, r]) => ({roundLabel: rl, round: r}))
    .sort((a, b) => (ROUND_ORDER[a.roundLabel] || 99) - (ROUND_ORDER[b.roundLabel] || 99));
  if (!rounds.length) return;
  const xAt = i => pad.l + (width - pad.l - pad.r) * (rounds.length === 1 ? .5 : i / (rounds.length - 1));
  const yAt = rank => pad.t + (rank - 1) / (opps.length - 1) * (height - pad.t - pad.b);
  drawAxes(ctx, width, height, pad, {lines: 8});
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 18px Georgia'; ctx.fillText('Every Opponent Rank Trajectory', pad.l, 24);
  rounds.forEach((r, i) => { const x = xAt(i); ctx.fillStyle = '#8ea3bf'; ctx.font = '13px Georgia'; ctx.save(); ctx.translate(x, height - 42); ctx.rotate(-0.45); ctx.textAlign = 'right'; ctx.fillText(r.round, 0, 0); ctx.restore(); });
  const colors = ['#c084fc','#ffd369','#4ade80','#f87171','#b07aa1','#76b7b2','#edc948','#e15759'];
  const highlightColors = ['#c084fc','#ffd369','#4ade80','#f87171','#f0abfc','#38bdf8','#fb923c','#c4b5fd'];
  let highlightIndex = 0;
  opps.forEach((o, oi) => {
    const rawMap = new Map((o.oppRanks || []).map(p => [p.roundLabel, p.rank]));
    // Build carry-forward map: fill gaps with last known rank
    const map = new Map();
    let lastRank = null;
    let firstSeen = false;
    rounds.forEach(r => {
      if (rawMap.has(r.roundLabel)) { lastRank = rawMap.get(r.roundLabel); firstSeen = true; }
      if (firstSeen && lastRank !== null) map.set(r.roundLabel, lastRank);
    });
    const isHi = highlightSet.has(o.name);
    const hiColor = highlightColors[highlightIndex % highlightColors.length];
    if (isHi) highlightIndex++;
    ctx.strokeStyle = isHi ? hiColor : colors[oi % colors.length];
    ctx.globalAlpha = isHi ? 1 : 0.16; ctx.lineWidth = isHi ? 4 : 1.2;
    ctx.beginPath(); let started = false;
    rounds.forEach((r, i) => {
      if (!map.has(r.roundLabel)) return;
      const x = xAt(i), y = yAt(map.get(r.roundLabel));
      started ? ctx.lineTo(x, y) : ctx.moveTo(x, y); started = true;
    });
    ctx.stroke(); ctx.globalAlpha = 1;
    if (isHi) {
      rounds.forEach((r, i) => {
        if (!map.has(r.roundLabel)) return;
        const x = xAt(i), y = yAt(map.get(r.roundLabel));
        const isReal = rawMap.has(r.roundLabel);
        ctx.fillStyle = hiColor; ctx.globalAlpha = isReal ? 1 : 0.4;
        ctx.beginPath(); ctx.arc(x, y, isReal ? 6 : 4, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1;
        if (isReal) { ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 12px Georgia'; ctx.fillText(map.get(r.roundLabel), x - 8, y - 11); }
      });
      const finalRank = map.get(rounds[rounds.length - 1].roundLabel);
      ctx.fillStyle = hiColor; ctx.font = 'bold 15px Georgia'; ctx.fillText(`${o.displayName || o.name} #${finalRank}`, width - pad.r + 20, yAt(finalRank) + 5);
    }
  });
}
const PARETO_METRICS = [
  {key: 'score', label: 'Total Score', dir: 'desc', format: v => Number(v).toFixed(2)},
  {key: 'rank', label: 'Current Rank', dir: 'asc', format: v => `#${v}`},
  {key: 'avgRank', label: 'Average Rank', dir: 'asc', format: v => Number(v).toFixed(1)},
  {key: 'winRate', label: 'Win Rate', dir: 'desc', format: v => `${Math.round(Number(v) * 100)}%`},
  {key: 'pointsPerMatch', label: 'Points / Match', dir: 'desc', format: v => Number(v).toFixed(3)},
  {key: 'rawPerformance', label: 'Raw Performance', dir: 'desc', format: v => Number(v).toFixed(3)},
  {key: 'overperformance', label: 'Overperformance', dir: 'desc', format: v => Number(v).toFixed(3)},
  {key: 'difficulty', label: 'Schedule Difficulty', dir: 'desc', format: v => Number(v).toFixed(2)},
  {key: 'scoreLost', label: 'Score Lost', dir: 'desc', format: v => Number(v).toFixed(3)},
  {key: 'adjustedScoreLost', label: 'Adjusted Score Lost', dir: 'desc', format: v => Number(v).toFixed(3)},
  {key: 'wins', label: 'Wins', dir: 'desc', format: v => `${v}`},
  {key: 'losses', label: 'Losses', dir: 'desc', format: v => `${v}`}
];
function drawHorizontalPareto(canvas, chars, metric) {
  if (!canvas || !chars.length) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width, height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  const sorted = chars.slice().sort((a, b) => metric.dir === 'asc' ? Number(a[metric.key]) - Number(b[metric.key]) : Number(b[metric.key]) - Number(a[metric.key]));
  const pad = {l: 250, r: 90, t: 42, b: 42};
  const rowH = (height - pad.t - pad.b) / sorted.length;
  const values = sorted.map(c => Math.abs(Number(c[metric.key]) || 0));
  const max = Math.max(1, ...values);
  ctx.fillStyle = '#e8edf6'; ctx.font = 'bold 18px Georgia'; ctx.fillText(`${metric.label} Pareto`, pad.l, 24);
  sorted.forEach((c, i) => {
    const y = pad.t + i * rowH;
    const value = Number(c[metric.key]) || 0;
    const w = Math.abs(value) / max * (width - pad.l - pad.r);
    ctx.fillStyle = i < 8 ? '#00c8ff' : (i < 24 ? '#ffd369' : '#4ade80');
    ctx.globalAlpha = i < 24 ? .86 : .55;
    ctx.fillRect(pad.l, y + 2, w, Math.max(3, rowH - 4));
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#8ea3bf'; ctx.font = '11px Georgia'; ctx.textAlign = 'right'; ctx.fillText(`${i + 1}. ${c.name}`, pad.l - 10, y + rowH * .68);
    ctx.textAlign = 'left'; ctx.fillStyle = '#e8edf6'; ctx.fillText(metric.format(value), pad.l + w + 8, y + rowH * .68);
  });
  ctx.textAlign = 'left';
}
function renderParetoTable(node, chars, metric) {
  if (!node) return;
  const sorted = chars.slice().sort((a, b) => metric.dir === 'asc' ? Number(a[metric.key]) - Number(b[metric.key]) : Number(b[metric.key]) - Number(a[metric.key]));
  node.innerHTML = sorted.slice(0, 24).map((c, i) => `<div class="pareto-row"><span>${i + 1}</span><a href="../${c.slug}/index.html">${c.displayName || c.name}</a><strong>${metric.format(c[metric.key])}</strong></div>`).join('');
}
(function init() {
  const data = pageData();
  if (data.characters && document.getElementById('overview-chart')) {
    const chars = data.characters.slice().sort((a, b) => a.rank - b.rank);
    // Build sorted round list from all characters' rank history
    const seenRds = new Map();
    chars.forEach(c => (c.ranks || []).forEach(r => { if (!seenRds.has(r.roundLabel)) seenRds.set(r.roundLabel, r.round); }));
    const roundList = Array.from(seenRds, ([rl, r]) => ({roundLabel: rl, round: r}))
      .sort((a, b) => (ROUND_ORDER[a.roundLabel] || 99) - (ROUND_ORDER[b.roundLabel] || 99));
    const defaultRound = roundList.length ? roundList[roundList.length - 1].roundLabel : 'current';

    function renderSmashRound(roundLabel) {
      document.querySelectorAll('.round-pill').forEach(btn => btn.classList.toggle('active', btn.dataset.round === roundLabel));
      let sorted;
      if (!roundLabel || roundLabel === 'current') {
        sorted = chars.map(c => ({...c, _rank: c.rank, _score: Number(c.score)}));
      } else {
        // Use the adjusted score from the rank entry (accounts for inter-round reductions)
        sorted = chars.map(c => {
          const rankEntry = (c.ranks || []).find(r => r.roundLabel === roundLabel);
          const adjustedScore = rankEntry ? Number(rankEntry.score) || 0 : 0;
          return {...c, _score: adjustedScore};
        }).filter(c => c._score > 0).sort((a, b) => b._score - a._score).map((c, i) => ({...c, _rank: i + 1}));
      }
      const leaderEl = document.getElementById('smash-leader-list');
      if (leaderEl) {
        leaderEl.innerHTML = sorted.map(c =>
          `<li><span>#${c._rank}</span><a href="${c.slug}/index.html">${c.displayName || c.name}</a><strong>${c._score.toFixed(2)}</strong></li>`
        ).join('');
      }
      const top16 = sorted.slice(0, 16);
      drawBarChart(document.getElementById('overview-chart'),
        top16.map(c => c.displayName || c.name),
        [{name: 'Score', color: css('--cyan'), alpha: .9, values: top16.map(c => c._score)}],
        'Top 16 Score Spread', 'Score', {hideLegend: true});
    }

    const pillsEl = document.getElementById('round-pills');
    if (pillsEl) {
      roundList.forEach(r => {
        const btn = document.createElement('button');
        btn.className = 'round-pill' + (r.roundLabel === defaultRound ? ' active' : '');
        btn.dataset.round = r.roundLabel;
        btn.textContent = r.round;
        btn.addEventListener('click', () => renderSmashRound(r.roundLabel));
        pillsEl.appendChild(btn);
      });
    }
    renderSmashRound(defaultRound);
  }
  if (data.opponents && document.getElementById('opp-overview-chart')) {
    const opps = data.opponents.slice(0, 16);
    drawBarChart(document.getElementById('opp-overview-chart'), opps.map(o => o.displayName || o.name), [{name: 'Total NT Score', color: '#c084fc', alpha: .9, values: opps.map(o => Number(o.totalNtScore))}], 'Top 16 Opponent NT Scores', 'Total NT Score', {hideLegend: true});
  }
  if (data.character) {
    const c = data.character;
    const name = c.displayName || c.name;
    const matchLabels = c.matches.map(m => `${m.round} M${m.match}`);
    const matchSeries = comparisonSeries(c).slice(0, 2).map(s => {
      const values = matchValueMap(s.character.matches);
      return {name: `${s.character.displayName || s.character.name} ${s.label}`, color: s.color, alpha: .62, values: matchLabels.map(label => values.get(label) || 0)};
    });
    matchSeries.push({name, color: css('--cyan'), alpha: .95, values: c.matches.map(m => m.score)});
    drawBarChart(document.getElementById('match-chart'), matchLabels, matchSeries, 'Score Per Match', 'Score', {line: {name: `${name} Total`, label: 'Total Score', color: css('--gold'), values: c.matches.map(m => m.accumulatedScore)}});
    drawRankComparisonChart(document.getElementById('rank-chart'), c, 'Rank Trajectory');
    const roundLabels = c.roundTotals.map(r => r.round);
    const roundSeries = comparisonSeries(c).slice(2, 4).map(s => {
      const values = roundValueMap(s.character.roundTotals);
      return {name: `${s.character.displayName || s.character.name} ${s.label}`, color: s.color, alpha: .62, values: roundLabels.map(label => values.get(label) || 0)};
    });
    roundSeries.splice(1, 0, {name, color: css('--cyan'), alpha: .95, values: c.roundTotals.map(r => r.score)});
    drawBarChart(document.getElementById('round-chart'), roundLabels, roundSeries, 'Round Score Totals vs. Rank ±5', 'Score');

    // ── Opponent section ──────────────────────────────────────────────────
    const opp = c.opponent;
    if (opp && opp.totalAppearances) {
      const kpiWrap = document.getElementById('opp-kpis');
      if (kpiWrap) {
        const kpis = [
          ['Appearances', opp.totalAppearances],
          ['W / L', `${opp.wins} / ${opp.losses}`],
          ['Win Rate', `${(opp.winRate * 100).toFixed(0)}%`],
          ['Total NT', opp.totalNtScore.toFixed(2)],
          ['Avg NT', opp.avgNtScore.toFixed(3)],
        ];
        kpiWrap.innerHTML = kpis.map(([lbl, val]) =>
          `<div class="opp-kpi"><strong>${val}</strong><span>${lbl}</span></div>`
        ).join('');
      }
      const oppCanvas = document.getElementById('opp-chart');
      if (oppCanvas && opp.appearances.length) {
        const oppLabels = opp.appearances.map(a => a.against);
        const oppVals = opp.appearances.map(a => a.ntScore);
        const oppColors = opp.appearances.map(a => a.win ? '#4ade80' : '#f87171');
        drawCustomBarChart(oppCanvas, oppLabels, oppVals, oppColors, 'NT Score Per Appearance as Opponent  (green = won)', 'NT Score');
      }
      const oppRoundCanvas = document.getElementById('opp-round-chart');
      if (oppRoundCanvas && opp.roundTotals.length) {
        const oppRoundLabels = opp.roundTotals.map(r => r.round);
        const oppRoundVals = opp.roundTotals.map(r => r.ntScore);
        drawCustomBarChart(oppRoundCanvas, oppRoundLabels, oppRoundVals, Array(oppRoundVals.length).fill('#c084fc'), 'NT Score by Round as Opponent', 'Total NT Score');
      }
      const logEl = document.getElementById('opp-log');
      if (logEl) {
        logEl.innerHTML = opp.appearances.map(a =>
          `<div class="opp-row"><span class="opp-round">${a.round} M${a.matchNum}</span><span class="${a.win ? 'opp-win' : 'opp-loss'}">${a.win ? 'W' : 'L'}</span><span>vs ${a.against}</span><span class="opp-nt">${a.ntScore.toFixed(2)}</span></div>`
        ).join('');
      }
    }
  }
  if (data.characters && document.getElementById('rank-atlas-chart')) {
    const select = document.getElementById('rank-highlight');
    const chars = data.characters.slice().sort((a, b) => a.rank - b.rank);
    select.innerHTML = chars.map(c => `<option value="${c.name}">${c.displayName || c.name} (#${c.rank})</option>`).join('');
    if (select.options.length) select.options[0].selected = true;
    const selectedNames = () => Array.from(select.selectedOptions).map(option => option.value);
    const redraw = () => drawRankAtlas(document.getElementById('rank-atlas-chart'), chars, selectedNames());
    select.addEventListener('change', redraw);
    redraw();
  }
  if (data.opponents && document.getElementById('opp-rank-atlas-chart')) {
    const select = document.getElementById('opp-rank-highlight');
    const opps = data.opponents.slice().sort((a, b) => a.oppRank - b.oppRank);
    select.innerHTML = opps.map(o => `<option value="${o.name}">${o.displayName || o.name} (#${o.oppRank})</option>`).join('');
    if (select.options.length) select.options[0].selected = true;
    const selectedNames = () => Array.from(select.selectedOptions).map(opt => opt.value);
    const redraw = () => drawOppRankAtlas(document.getElementById('opp-rank-atlas-chart'), opps, selectedNames());
    select.addEventListener('change', redraw);
    redraw();
  }
  if (data.characters && document.getElementById('score-atlas-chart')) {
    const select = document.getElementById('score-highlight');
    const chars = data.characters.slice().sort((a, b) => a.rank - b.rank);
    select.innerHTML = chars.map(c => `<option value="${c.name}">${c.displayName || c.name} (#${c.rank})</option>`).join('');
    if (select.options.length) select.options[0].selected = true;
    const selectedNames = () => Array.from(select.selectedOptions).map(option => option.value);
    const redraw = () => drawScoreAtlas(document.getElementById('score-atlas-chart'), chars, selectedNames());
    select.addEventListener('change', redraw);
    redraw();
  }
  if (data.characters && document.getElementById('pareto-chart')) {
    const select = document.getElementById('pareto-metric');
    select.innerHTML = PARETO_METRICS.map(m => `<option value="${m.key}">${m.label}</option>`).join('');
    const redraw = () => {
      const metric = PARETO_METRICS.find(m => m.key === select.value) || PARETO_METRICS[0];
      document.getElementById('pareto-title').textContent = metric.label;
      drawHorizontalPareto(document.getElementById('pareto-chart'), data.characters, metric);
      renderParetoTable(document.getElementById('pareto-table'), data.characters, metric);
    };
    select.addEventListener('change', redraw);
    redraw();
  }
})();
""".strip(),
    )


def main() -> None:
    ensure_dirs()
    crop_icon_sheet()
    profiles = build_profiles(RECORDS_DIR, MATCHUP_DF)
    opponent_profiles = build_opponent_profiles(RECORDS_DIR)
    difficulty_map = compute_difficulty(profiles, MATCHUP_DF, w=0.5)
    copy_first_ssbu_icons(list(profiles.keys()))
    create_fallback_icons(list(profiles.keys()))
    characters = [profile_payload(profile, profiles, opponent_profiles, difficulty_map) for profile in profiles.values()]
    characters.sort(key=lambda item: (int(item["rank"]), str(item["name"])))
    attach_character_comparisons(characters)

    write_styles()
    write_script()
    write_text(SITE_DIR / "index.html", home_page())
    for slug, label, _symbol in CATEGORY_PAGES:
      write_text(SITE_DIR / slug / "index.html", category_page(label))
    write_text(SMASH_DIR / "index.html", smash_page(characters))
    write_text(SMASH_DIR / "Rank-Atlas" / "index.html", rank_atlas_page(characters))
    write_text(SMASH_DIR / "Score-Atlas" / "index.html", score_atlas_page(characters))
    write_text(SMASH_DIR / "Paretos" / "index.html", paretos_page(characters))
    write_text(PDF_OUT_DIR / "index.html", pdf_index_page(characters))

    # Build opponent leaderboard (sorted by total NT score desc, no multipliers)
    opp_leaders: list[dict] = [
        {
            "name": c["name"],
            "displayName": c.get("displayName", c["name"]),
            "slug": c["slug"],
            "icon": c.get("icon"),
            "model": c.get("model"),
            "oppRank": 0,
            "totalNtScore": float((c.get("opponent") or {}).get("totalNtScore", 0) or 0),
            "wins": int((c.get("opponent") or {}).get("wins", 0) or 0),
            "losses": int((c.get("opponent") or {}).get("losses", 0) or 0),
            "winRate": float((c.get("opponent") or {}).get("winRate", 0) or 0),
            "appearances": int((c.get("opponent") or {}).get("totalAppearances", 0) or 0),
            "avgNtScore": float((c.get("opponent") or {}).get("avgNtScore", 0) or 0),
        }
        for c in characters
    ]
    opp_leaders.sort(key=lambda x: -x["totalNtScore"])
    for i, o in enumerate(opp_leaders):
        o["oppRank"] = i + 1

    # Build opponent rank trajectory (cumulative NT score per round → rank at each round)
    _ROUND_ORDER_LABELS = ["round_1", "round_2", "elimination_1", "round_3", "elimination_2", "round_4", "elimination_3", "round_5"]
    opp_cumul: dict[str, dict[str, float]] = {}
    for opp_profile in opponent_profiles.values():
        name = opp_profile.name
        cumul = 0.0
        opp_cumul[name] = {}
        for lbl in _ROUND_ORDER_LABELS:
            if lbl in opp_profile.nt_score_by_round:
                cumul += opp_profile.nt_score_by_round[lbl]
                opp_cumul[name][lbl] = round(cumul, 3)
    opp_rank_at: dict[str, dict[str, int]] = {}
    for lbl in _ROUND_ORDER_LABELS:
        scored = [(nm, opp_cumul[nm][lbl]) for nm in opp_cumul if lbl in opp_cumul[nm]]
        if not scored:
            continue
        scored.sort(key=lambda x: -x[1])
        for rank, (nm, _) in enumerate(scored, 1):
            opp_rank_at.setdefault(nm, {})[lbl] = rank
    for o in opp_leaders:
        nm = o["name"]
        o["oppRanks"] = [
            {"roundLabel": lbl, "round": ROUND_DISPLAY.get(LABEL_TO_ROUND.get(lbl, 0), lbl), "rank": r}
            for lbl, r in opp_rank_at.get(nm, {}).items()
        ]

    write_text(SMASH_DIR / "Opponents" / "index.html", opponents_page(opp_leaders))
    write_text(SMASH_DIR / "Opponents" / "Rank-Atlas" / "index.html", opp_rank_atlas_page(opp_leaders))

    # Generate individual opponent profile pages
    char_by_name = {c["name"]: c for c in characters}
    for o in opp_leaders:
        char = char_by_name.get(o["name"])
        if char and int((char.get("opponent") or {}).get("totalAppearances", 0) or 0) > 0:
            char["oppRank"] = o["oppRank"]
            write_text(SMASH_DIR / "Opponents" / str(char["slug"]) / "index.html", opponent_character_page(char))

    for character in characters:
        write_text(SMASH_DIR / str(character["slug"]) / "index.html", character_page(character))

    print(f"Generated static site: {SITE_DIR}")
    print(f"Character pages: {len(characters)}")


if __name__ == "__main__":
    main()
