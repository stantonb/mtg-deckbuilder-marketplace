#!/usr/bin/env python3
"""Card validator and cache manager backed by the Scryfall API.

The cache (MTG_Card_Cache.json in the skill directory) is the single source
of truth for card data. Cache-first policy: a cached card is trusted as-is
and never re-fetched. Misses are validated against Scryfall in batches of 75
via POST /cards/collection (never from model memory). Lookup failures are
reported with fuzzy-match suggestions — a card is never guessed at and never
silently dropped.

Usage:
  card_cache.py validate --collection collection.json --out enriched.json
  card_cache.py lookup "Lightning Bolt" "Firespout" [--no-fetch]
  card_cache.py stats

Exit codes: 0 ok; 2 = one or more cards could not be validated (see the
"problems" list in the output — resolve these with the user before building).
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

from mtglib import (BASIC_COLORS, CACHE_PATH, cache_index, load_cache, norm,
                    resolve, save_cache)

API = "https://api.scryfall.com"
HEADERS = {
    "User-Agent": "mtg-deckbuilder-claude-skill/1.0",
    "Accept": "application/json",
}
BATCH_SIZE = 75
DELAY = 0.12  # Scryfall asks for 50-100ms between requests


def _request(url, payload=None, retries=4):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = dict(HEADERS)
    if data:
        headers["Content-Type"] = "application/json"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  Scryfall {e.code}; backing off {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def make_record(card, owned_printing=None):
    """Trim a Scryfall card object to the fields the skill needs."""
    faces = card.get("card_faces") or []

    def joined(field):
        vals = [f.get(field) for f in faces if f.get(field)]
        return " // ".join(vals) if vals else card.get(field)

    front = faces[0] if faces else card
    rec = {
        "name": card["name"],
        "mana_cost": card.get("mana_cost") if card.get("mana_cost") is not None
                     else joined("mana_cost"),
        "cmc": card.get("cmc"),
        "colors": card.get("colors", front.get("colors", [])),
        "color_identity": card.get("color_identity", []),
        "type_line": card.get("type_line") or joined("type_line"),
        "oracle_text": joined("oracle_text") or "",
        "power": front.get("power"),
        "toughness": front.get("toughness"),
        "loyalty": front.get("loyalty"),
        "keywords": card.get("keywords", []),
        "rarity": card.get("rarity"),
        "set": card.get("set"),
        "collector_number": card.get("collector_number"),
        "legalities": card.get("legalities", {}),
        "prices": card.get("prices", {}),
        "produced_mana": card.get("produced_mana", []),
        "layout": card.get("layout"),
        "scryfall_id": card.get("id"),
        "is_basic": "Basic Land" in (card.get("type_line") or ""),
        "validated_at": date.today().isoformat(),
    }
    if faces:
        rec["card_faces"] = [{
            "name": f.get("name"), "mana_cost": f.get("mana_cost"),
            "type_line": f.get("type_line"), "oracle_text": f.get("oracle_text"),
            "power": f.get("power"), "toughness": f.get("toughness"),
            "loyalty": f.get("loyalty"), "colors": f.get("colors", []),
        } for f in faces]
    if owned_printing and owned_printing.get("set"):
        rec["owned_set"] = owned_printing["set"]
        rec["owned_collector_number"] = owned_printing.get("collector_number")
    return rec


def fetch_batch(names):
    """POST /cards/collection for up to 75 names. Returns (found, not_found)."""
    found, not_found = [], []
    for i in range(0, len(names), BATCH_SIZE):
        chunk = names[i:i + BATCH_SIZE]
        payload = {"identifiers": [{"name": n} for n in chunk]}
        result = _request(f"{API}/cards/collection", payload)
        found.extend(result.get("data", []))
        not_found.extend(nf.get("name") for nf in result.get("not_found", []))
        time.sleep(DELAY)
    return found, not_found


def fuzzy_suggest(name):
    """Closest-match suggestions for a failed lookup (fuzzy + autocomplete)."""
    suggestions = []
    enc = urllib.parse.quote(name)
    hit = _request(f"{API}/cards/named?fuzzy={enc}")
    time.sleep(DELAY)
    if hit and hit.get("object") == "card":
        suggestions.append(hit["name"])
    ac = _request(f"{API}/cards/autocomplete?q={enc}")
    time.sleep(DELAY)
    if ac:
        for s in ac.get("data", [])[:5]:
            if s not in suggestions:
                suggestions.append(s)
    return suggestions


def ensure_cached(cache, names, no_fetch=False):
    """Ensure every name is in the cache. Returns (hits, fetched, problems)."""
    idx = cache_index(cache)
    hits, misses = [], []
    seen = set()
    for n in names:
        k = norm(n)
        if k in seen:
            continue
        seen.add(k)
        (hits if resolve(idx, n) else misses).append(n)

    problems, fetched = [], []
    if misses and no_fetch:
        problems = [{"name": n, "reason": "not in cache (fetching disabled)",
                     "suggestions": []} for n in misses]
    elif misses:
        found, not_found = fetch_batch(misses)
        by_req_name = {}
        for card in found:
            cache["cards"][norm(card["name"])] = make_record(card)
            fetched.append(card["name"])
            by_req_name[norm(card["name"].split(" // ")[0])] = card["name"]
        for n in not_found:
            if n is None:
                continue
            problems.append({
                "name": n,
                "reason": "not found on Scryfall — possible typo",
                "suggestions": fuzzy_suggest(n),
            })
    return hits, fetched, problems


def cmd_validate(args):
    coll = json.loads(Path(args.collection).read_text(encoding="utf-8-sig"))
    cache = load_cache(args.cache)
    names = [c["name"] for c in coll["cards"]]
    # Basics are always needed for deckbuilding; cache them once, forever.
    basics = ["Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"]
    hits, fetched, problems = ensure_cached(
        cache, names + basics, no_fetch=args.no_fetch)

    idx = cache_index(cache)
    enriched_cards = []
    annotated = False
    for c in coll["cards"]:
        rec = resolve(idx, c["name"])
        if rec and c.get("set") and not rec.get("owned_set"):
            rec["owned_set"] = c["set"]
            rec["owned_collector_number"] = c.get("collector_number")
            annotated = True
        enriched_cards.append({**c, "card": rec})
    if fetched or annotated:
        save_cache(cache, args.cache)

    result = {
        "collection_csv": coll.get("csv_path"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "cache_hits": len(hits),
        "fetched_from_scryfall": len(fetched),
        "problems": problems,
        "cards": enriched_cards,
    }
    out = json.dumps(result, indent=1)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    else:
        print(out)
    print(f"Validated {len(names)} names: {len(hits)} from cache, "
          f"{len(fetched)} fetched from Scryfall, {len(problems)} problems.",
          file=sys.stderr)
    for p in problems:
        sugg = ", ".join(p["suggestions"]) or "no close matches"
        print(f"  PROBLEM: {p['name']!r} — {p['reason']}. "
              f"Did you mean: {sugg}?", file=sys.stderr)
    sys.exit(2 if problems else 0)


def cmd_lookup(args):
    cache = load_cache(args.cache)
    hits, fetched, problems = ensure_cached(cache, args.names,
                                            no_fetch=args.no_fetch)
    if fetched:
        save_cache(cache, args.cache)
    idx = cache_index(cache)
    out = {n: resolve(idx, n) for n in args.names}
    print(json.dumps(out, indent=1))
    if problems:
        for p in problems:
            sugg = ", ".join(p["suggestions"]) or "no close matches"
            print(f"PROBLEM: {p['name']!r} — {p['reason']}. Did you mean: {sugg}?",
                  file=sys.stderr)
        sys.exit(2)


def cmd_stats(args):
    cache = load_cache(args.cache)
    cards = cache.get("cards", {})
    print(json.dumps({
        "cache_path": str(Path(args.cache) if args.cache else CACHE_PATH),
        "cards_cached": len(cards),
        "meta": cache.get("_meta", {}),
    }, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", help=f"cache path (default {CACHE_PATH})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="validate a collection JSON (from parse_collection.py)")
    v.add_argument("--collection", required=True)
    v.add_argument("--out", help="write enriched collection JSON here")
    v.add_argument("--no-fetch", action="store_true",
                   help="cache-only; report misses instead of fetching")
    v.set_defaults(func=cmd_validate)

    l = sub.add_parser("lookup", help="look up specific card names")
    l.add_argument("names", nargs="+")
    l.add_argument("--no-fetch", action="store_true")
    l.set_defaults(func=cmd_lookup)

    s = sub.add_parser("stats", help="cache statistics")
    s.set_defaults(func=cmd_stats)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
