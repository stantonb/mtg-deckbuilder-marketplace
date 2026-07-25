#!/usr/bin/env python3
"""Deck quality gates: ownership, size, copy limits, legality, restrictions.

Checks a decklist against the enriched collection (from card_cache.py) and
the format rules. All gates must pass before a deck is shown to the user.
On pass, --export writes a timestamped Moxfield-importable .txt
("N Card Name (SET) collector-number") so re-runs never overwrite earlier
builds, and --ledger tracks copies used across decks for the
"simultaneous" multi-deck overlap policy.

Usage:
  validate_deck.py --deck deck.txt --enriched enriched.json --format limited \
      [--deck-size 40] [--restrict-set ecl] [--ledger ledger.json] \
      [--commander "Name"] [--ban "A;B"] [--require "C;D"] \
      [--export-dir "outdir" --deck-name "My Deck"]

Exit codes: 0 all gates pass; 1 one or more gates failed.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from mtglib import cache_index, is_basic, load_cache, norm, parse_decklist, resolve

FORMATS = {
    # size: (exact, n) or (min, n); copies: max per name (None = pool-bound);
    # legality: Scryfall legalities key (None = no legality check)
    "commander": {"size": ("exact", 100), "copies": 1, "legality": "commander",
                  "commander": True, "sideboard": 0},
    "standard":  {"size": ("min", 60), "copies": 4, "legality": "standard", "sideboard": 15},
    "modern":    {"size": ("min", 60), "copies": 4, "legality": "modern", "sideboard": 15},
    "pioneer":   {"size": ("min", 60), "copies": 4, "legality": "pioneer", "sideboard": 15},
    "legacy":    {"size": ("min", 60), "copies": 4, "legality": "legacy", "sideboard": 15},
    "pauper":    {"size": ("min", 60), "copies": 4, "legality": "pauper", "sideboard": 15},
    "limited":   {"size": ("exact", 40), "copies": None, "legality": None, "sideboard": None},
    "kitchen":   {"size": ("min", 60), "copies": 4, "legality": None, "sideboard": None},
}
ALIASES = {"edh": "commander", "league": "limited", "sealed": "limited",
           "draft": "limited", "casual": "kitchen", "kitchen table": "kitchen"}


def load_owned(enriched_path):
    data = json.loads(Path(enriched_path).read_text(encoding="utf-8-sig"))
    owned = {}
    for c in data["cards"]:
        rec = c.get("card")
        keys = {norm(c["name"])}
        if rec:
            keys.add(norm(rec["name"]))
            if " // " in rec["name"]:
                keys.add(norm(rec["name"].split(" // ")[0]))
        entry = {"count": c["count"], "printings": c["printings"],
                 "set": c.get("set"), "collector_number": c.get("collector_number"),
                 "card": rec, "csv_name": c["name"]}
        for k in keys:
            owned.setdefault(k, entry)
    return owned, data


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", required=True, help="decklist .txt ('N Name' lines)")
    ap.add_argument("--enriched", required=True, help="enriched.json from card_cache.py validate")
    ap.add_argument("--format", required=True)
    ap.add_argument("--deck-size", type=int, help="exact main-deck size override")
    ap.add_argument("--max-copies", type=int, help="copy-limit override")
    ap.add_argument("--commander", help="commander name (commander format)")
    ap.add_argument("--restrict-set", help="every nonbasic card must be owned in this set code")
    ap.add_argument("--ban", default="", help="';'-separated banned names")
    ap.add_argument("--require", default="", help="';'-separated must-include names")
    ap.add_argument("--ledger", help="ledger JSON tracking copies used across decks "
                                     "(simultaneous overlap policy)")
    ap.add_argument("--export-dir", help="on pass, write timestamped Moxfield .txt here")
    ap.add_argument("--deck-name", default="Deck")
    ap.add_argument("--cache", help="cache path override")
    ap.add_argument("--json", action="store_true", help="emit JSON result")
    args = ap.parse_args()

    fmt_name = ALIASES.get(args.format.lower(), args.format.lower())
    if fmt_name not in FORMATS:
        sys.exit(f"ERROR: unknown format {args.format!r}. "
                 f"Known: {sorted(FORMATS) + sorted(ALIASES)}")
    fmt = FORMATS[fmt_name]

    main_deck, side, parse_errors = parse_decklist(args.deck)
    owned, enriched = load_owned(args.enriched)
    idx = cache_index(load_cache(args.cache))

    failures, warnings = [], []
    for line in parse_errors:
        failures.append(f"unparseable decklist line: {line!r}")

    ledger_used = {}
    if args.ledger and Path(args.ledger).exists():
        ledger_used = json.loads(Path(args.ledger).read_text())["used"]

    # --- resolve every card, aggregate counts across main+side
    all_cards = {}
    for zone, cards in (("main", main_deck), ("side", side)):
        for c in cards:
            k = norm(c["name"])
            e = all_cards.setdefault(k, {"name": c["name"], "main": 0, "side": 0})
            e[zone] += c["count"]

    main_size = sum(c["count"] for c in main_deck)
    side_size = sum(c["count"] for c in side)

    # --- gate: size
    kind, n = fmt["size"]
    size_target = args.deck_size or n
    if args.deck_size or kind == "exact":
        if main_size != size_target:
            failures.append(f"deck size {main_size} != required {size_target}")
    elif main_size < n:
        failures.append(f"deck size {main_size} < format minimum {n}")
    elif main_size > n:
        warnings.append(f"deck size {main_size} exceeds the {n}-card minimum — "
                        "usually worse consistency; justify in the report")
    if fmt["sideboard"] is not None and side_size > fmt["sideboard"]:
        failures.append(f"sideboard {side_size} > allowed {fmt['sideboard']}")

    commander_rec = None
    if fmt.get("commander"):
        if not args.commander:
            failures.append("commander format requires --commander")
        else:
            commander_rec = resolve(idx, args.commander)
            if not commander_rec:
                failures.append(f"commander {args.commander!r} not in card cache")
            elif norm(args.commander) not in all_cards:
                failures.append(f"commander {args.commander!r} must appear in the decklist")

    banned = {norm(b) for b in args.ban.split(";") if b.strip()}
    required = {norm(r) for r in args.require.split(";") if r.strip()}
    copy_limit = args.max_copies if args.max_copies else fmt["copies"]

    for k, e in all_cards.items():
        total = e["main"] + e["side"]
        name = e["name"]
        basic = is_basic(name)
        rec = resolve(idx, name)
        own = owned.get(k)

        # gate: oracle-verified card data exists for every card
        if rec is None and not basic:
            failures.append(f"{name}: no verified card data in cache — "
                            "run card_cache.py before building")
            continue

        # gate: ownership (basics exempt — unlimited in every format/league)
        if not basic:
            if own is None:
                failures.append(f"{name}: not in the collection")
                continue
            available = own["count"] - ledger_used.get(k, 0)
            if total > available:
                held = f" ({ledger_used.get(k, 0)} already used by other decks)" \
                    if ledger_used.get(k) else ""
                failures.append(f"{name}: {total} in deck > {available} available"
                                f"{held}")

        # gate: copy limit
        if copy_limit and not basic and total > copy_limit:
            failures.append(f"{name}: {total} copies > limit {copy_limit}")

        # gate: format legality (from verified cache data, never memory)
        if fmt["legality"] and rec:
            status = (rec.get("legalities") or {}).get(fmt["legality"], "unknown")
            if status == "restricted" and total > 1:
                failures.append(f"{name}: restricted in {fmt_name} (max 1)")
            elif status not in ("legal", "restricted"):
                failures.append(f"{name}: {status} in {fmt_name}")

        # gate: color identity (commander)
        if commander_rec and rec:
            ci = set(rec.get("color_identity", []))
            if not ci <= set(commander_rec.get("color_identity", [])):
                failures.append(f"{name}: color identity {sorted(ci)} outside "
                                f"commander's {commander_rec['color_identity']}")

        # gate: set restriction (owned printings in that set must cover the count)
        if args.restrict_set and not basic and own:
            in_set = sum(p["count"] for p in own["printings"]
                         if p["set"] == args.restrict_set.lower())
            if total > in_set:
                failures.append(f"{name}: {total} used but only {in_set} owned "
                                f"in set {args.restrict_set!r}")

        if k in banned:
            failures.append(f"{name}: on the ban list for this build")

    for r in required:
        if r not in all_cards:
            failures.append(f"required card missing from deck: {r!r}")

    result = {
        "deck": args.deck, "format": fmt_name, "main_size": main_size,
        "sideboard_size": side_size, "distinct": len(all_cards),
        "passed": not failures, "failures": failures, "warnings": warnings,
    }

    exported = None
    if not failures and args.export_dir:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = Path(args.export_dir) / f"{args.deck_name} {stamp}.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for zone, cards in (("main", main_deck), ("side", side)):
            if zone == "side" and cards:
                lines.append("")
                lines.append("Sideboard:")
            for c in cards:
                own = owned.get(norm(c["name"]))
                rec = resolve(idx, c["name"])
                display = rec["name"] if rec else c["name"]
                if is_basic(c["name"]) or not own or not own.get("set"):
                    lines.append(f"{c['count']} {display}")
                else:
                    setc, cn = own["set"], own["collector_number"]
                    if args.restrict_set:
                        for p in own["printings"]:
                            if p["set"] == args.restrict_set.lower():
                                setc, cn = p["set"], p["collector_number"]
                                break
                    lines.append(f"{c['count']} {display} ({setc.upper()}) {cn}")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        exported = str(out)
        result["exported"] = exported

        if args.ledger:
            for k, e in all_cards.items():
                if not is_basic(e["name"]):
                    ledger_used[k] = ledger_used.get(k, 0) + e["main"] + e["side"]
            Path(args.ledger).write_text(
                json.dumps({"used": ledger_used}, indent=1), encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=1))
    else:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {args.deck_name}: {main_size} main / {side_size} side, "
              f"{len(all_cards)} distinct, format={fmt_name}")
        for f in failures:
            print(f"  FAIL: {f}")
        for w in warnings:
            print(f"  warn: {w}")
        if exported:
            print(f"  exported -> {exported}")
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
