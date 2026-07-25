"""Shared helpers for the mtg-deckbuilder skill scripts.

All scripts in this directory import from here. The card cache lives in the
skill directory (one cache shared by every project): MTG_Card_Cache.json.
"""
import json
import os
import re
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
# MTG_CARD_CACHE env var overrides the default location — useful when the
# skill ships inside a plugin (plugin dirs are replaced on update) or to
# share one cache across installs.
CACHE_PATH = Path(os.environ.get("MTG_CARD_CACHE",
                                 SKILL_DIR / "MTG_Card_Cache.json"))

# Basic lands are always available in unlimited quantity in every sanctioned
# format (and leagues supply them), so they are exempt from ownership checks.
BASIC_COLORS = {
    "plains": "W", "island": "U", "swamp": "B", "mountain": "R",
    "forest": "G", "wastes": "C",
    "snow-covered plains": "W", "snow-covered island": "U",
    "snow-covered swamp": "B", "snow-covered mountain": "R",
    "snow-covered forest": "G", "snow-covered wastes": "C",
}


def norm(name: str) -> str:
    """Normalise a card name for matching: lowercase, collapsed whitespace."""
    return " ".join(name.strip().lower().split())


def is_basic(name: str) -> bool:
    return norm(name) in BASIC_COLORS


def load_cache(path=None) -> dict:
    p = Path(path) if path else CACHE_PATH
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"_meta": {"created": date.today().isoformat()}, "cards": {}}


def save_cache(cache: dict, path=None) -> None:
    p = Path(path) if path else CACHE_PATH
    cache.setdefault("_meta", {})["updated"] = date.today().isoformat()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(p)


def cache_index(cache: dict) -> dict:
    """name-key -> record, with front-face aliases for double-faced/split cards
    so 'Fable of the Mirror-Breaker' finds 'Fable ... // Reflection ...'."""
    idx = {}
    for key, rec in cache.get("cards", {}).items():
        idx[key] = rec
    for key, rec in cache.get("cards", {}).items():
        if " // " in rec.get("name", ""):
            front = norm(rec["name"].split(" // ")[0])
            idx.setdefault(front, rec)
    return idx


def resolve(idx: dict, name: str):
    return idx.get(norm(name))


# Decklist lines: "4 Lightning Bolt", "1x Sol Ring", "2 Firespout (ECL) 142".
_DECK_LINE = re.compile(
    r"^\s*(\d+)\s*[xX]?\s+(.+?)"
    r"(?:\s+\(([A-Za-z0-9]{2,6})\)\s*([\w\-★\*]+)?)?\s*$"
)
_SIDEBOARD = re.compile(r"^\s*sideboard\b:?\s*$", re.IGNORECASE)


def parse_decklist(path):
    """Parse a decklist text file.

    Returns (main, side, errors) where main/side are lists of dicts
    {count, name, set, collector_number} and errors is a list of unparseable
    non-empty lines. Lines starting with '#' or '//' are comments; a bare
    'Sideboard' line switches to the sideboard section.
    """
    main, side, errors = [], [], []
    target = main
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        if _SIDEBOARD.match(line):
            target = side
            continue
        m = _DECK_LINE.match(line)
        if not m:
            errors.append(raw)
            continue
        count, name, setcode, cn = m.groups()
        target.append({
            "count": int(count),
            "name": name.strip(),
            "set": setcode.lower() if setcode else None,
            "collector_number": cn,
        })
    return main, side, errors


_SYMBOL = re.compile(r"\{([^}]+)\}")


def parse_mana_cost(cost: str):
    """'{2}{W}{W}' -> (generic=2, pips=[{'W'},{'W'}]).

    Each pip is the set of colors that can pay it (hybrid pips have two).
    Phyrexian pips count as their colored half (payable with life anyway, so
    this is the conservative reading for colour-screw checks). {X} adds 0.
    """
    generic, pips = 0, []
    for sym in _SYMBOL.findall(cost or ""):
        parts = [p for p in sym.split("/") if p != "P"]
        if len(parts) == 1 and parts[0].isdigit():
            generic += int(parts[0])
        elif len(parts) == 1 and parts[0] in "WUBRGC":
            pips.append(frozenset(parts[0]))
        elif len(parts) == 1 and parts[0] == "X":
            continue
        elif len(parts) == 2 and parts[0].isdigit() and parts[1] in "WUBRGC":
            # Twobrid {2/W}: payable as generic; treat as generic 2 for
            # castability (cheapest honest reading is the colour, but generic
            # never colour-screws, so count the colour as optional).
            pips.append(frozenset(parts[1]))
        elif all(p in "WUBRGC" for p in parts):
            pips.append(frozenset(parts))
        # snow {S}, energy etc. are ignored for goldfish purposes
    return generic, pips


def card_is_land(rec: dict) -> bool:
    return "Land" in (rec.get("type_line") or "").split("//")[0]


def land_produces(rec: dict) -> frozenset:
    prod = rec.get("produced_mana")
    if prod:
        return frozenset(c for c in prod if c in "WUBRGC")
    b = BASIC_COLORS.get(norm(rec.get("name", "")))
    return frozenset(b) if b else frozenset()


def land_etb_tapped(rec: dict) -> bool:
    """True for lands that always enter tapped ('unless' clauses are treated
    as untapped — optimistic, noted in simulator output)."""
    text = (rec.get("oracle_text") or "").lower()
    if "unless" in text:
        return False
    return bool(re.search(r"enters (the battlefield )?tapped", text))


def synthetic_basic(name: str) -> dict:
    """Minimal record for a basic land when it is not in the cache yet."""
    color = BASIC_COLORS[norm(name)]
    return {
        "name": name.title(), "mana_cost": "", "cmc": 0.0,
        "colors": [], "color_identity": [] if color == "C" else [color],
        "type_line": "Basic Land", "oracle_text": f"({{T}}: Add {{{color}}}.)",
        "keywords": [], "rarity": "common", "set": "", "collector_number": "",
        "legalities": {}, "prices": {}, "produced_mana": [color],
        "layout": "normal", "is_basic": True, "validated_at": None,
        "synthetic": True,
    }
