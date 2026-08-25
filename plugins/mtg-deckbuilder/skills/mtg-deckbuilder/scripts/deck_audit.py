#!/usr/bin/env python3
"""Role audit: counts a decklist's functional packages (lands, ramp, card
advantage, spot removal, sweepers, counterspells, tutors, protection,
creatures, token makers) from verified oracle text and compares them with
the target ranges for the chosen template.

This is an ADVISORY tool: the classification is keyword-based and prints
every card's roles so the deckbuilder can override a misread. Exit code is
always 0 unless the input is unusable. Card data comes from the enriched
collection / cache, never from memory.

Templates (ranges are inclusive; nonland counts are per deck):
  commander                 100-card singleton, 3+ opponents
  sixty --archetype X       60-card constructed (aggro/midrange/control/combo)
  limited                   40-card league/sealed/draft

Usage:
  deck_audit.py --deck deck.txt --enriched enriched.json --template commander \
      [--commander "Name"] [--archetype midrange] [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

from mtglib import (cache_index, card_is_land, is_basic, load_cache, norm,
                    parse_decklist, resolve, synthetic_basic)

PERMANENT_TYPES = ("Artifact", "Creature", "Enchantment", "Planeswalker", "Battle")

# Ordered (role, compiled regex) pairs applied to the lower-cased oracle text.
# A card can carry several roles.
RULES = {
    "ramp": [
        r"search your library for [^.]*land card[^.]*?put [^.]*onto the battlefield",
        r"put a land card from your hand onto the battlefield",
        r"you may play an additional land",
        r"spells? you cast cost \{\d\} less",
        r"(creature|artifact|enchantment|instant|sorcery|noncreature|planeswalker|legendary)[a-z, ]* spells (you cast )?cost \{\d\} less",
    ],
    "draw": [
        r"draws? (a|two|three|four|x|\d+|that many|cards? equal) cards?",
        r"draw a card for each",
        r"look at the top [^.]*put [^.]*into your hand",
        r"exile the top [^.]*you may (play|cast) (it|that card|them|those cards)",
        r"reveal the top [^.]*put [^.]*into your hand",
        r"each player draws",
    ],
    "recursion": [
        r"return [^.]*card[^.]*from (your|a) graveyard to (your hand|the battlefield)",
        r"return [^.]*card[^.]*from among them to your hand",
        r"you may cast [^.]*from your graveyard",
    ],
    "tutor": [
        r"search your library for (a|an|up to \w+) (card|creature card|instant|sorcery|artifact|enchantment|planeswalker|legendary|noncreature|nonland|permanent)",
    ],
    "spot_removal": [
        r"destroy (target|up to \w+ target|another target)",
        r"exile (target|up to \w+ target|another target) (\w+ )?(creature|artifact|enchantment|permanent|nonland|planeswalker|player|opponent)",
        r"deals? (\d+|x) damage to (any target|(up to \w+ )?target (\w+ )?(creature|planeswalker|player|opponent))",
        r"deals? damage equal to [^.]*to (any target|(up to \w+ )?target (\w+ )?creature)",
        r"target creature (an opponent controls )?gets -(\d+|x)/-(\d+|x)",
        r"fights? (up to one )?(another )?target creature",
        r"return (target|up to \w+ target|another target|those|both|them|these) [^.]*to (its|their) owners?'? hands?",
        r"(target|each) (player|opponent) sacrifices a creature",
        r"puts? (it|target [^.]*|that card) (into|on) (their|its owner's|the) library",
        r"put (target|up to \w+ target) creature[^.]*(on top|on the bottom) of",
        r"enchanted (creature|permanent) can't attack or block",
        r"tap target creature[^.]*doesn't untap",
        r"gain control of target",
    ],
    "sweeper": [
        r"destroy all (creatures|nonland permanents|artifacts|enchantments|permanents|other)",
        r"exile all (creatures|nonland permanents|permanents|other)",
        r"deals? (\d+|x) damage to each (creature|opponent and each creature|other creature)",
        r"(all|each) (other )?creatures? gets? -(\d+|x)/-(\d+|x)",
        r"put [^.]*-\d+/-\d+ counters? on each (creature|other creature)",
        r"each player sacrifices (all|half|\w+) (creatures|permanents|nonland)",
        r"return all (creatures|nonland permanents|permanents)",
        r"destroy each (creature|nonland permanent)",
    ],
    "counterspell": [
        r"counter target (spell|noncreature spell|creature spell|instant|sorcery|activated|triggered|ability)",
    ],
    "protection": [
        r"gains? [^.]*(hexproof|indestructible|shroud)",
        r"protection from",
        r"(creatures|permanents) you control (gain|have) (hexproof|indestructible)",
        r"counter target spell that targets",
        r"regenerate",
        r"phase(s)? out",
        r"can't be countered",
    ],
    "token_maker": [
        r"create (a|an|two|three|four|x|\d+|that many) [^.]*tokens?",
    ],
    "lifegain": [
        r"you gain \d+ life",
        r"lifelink",
    ],
    "graveyard_hate": [
        r"exile (target player's|each player's|all cards from all|all graveyards|all cards from target player's) graveyard",
        r"exile (target|up to \w+ target) cards? from (a|target|an opponent's) graveyard",
    ],
}
COMPILED = {role: [re.compile(p) for p in pats] for role, pats in RULES.items()}

TEMPLATES = {
    "commander": {
        "lands": (35, 40), "ramp": (8, 12), "card_advantage": (8, 12),
        "spot_removal": (6, 10), "sweeper": (2, 4), "interaction": (10, 16),
        "creatures": (18, 32), "avg_mv_max": 3.6,
    },
    "sixty": {
        "aggro":    {"lands": (18, 22), "interaction": (4, 8), "creatures": (20, 30),
                     "card_advantage": (0, 6), "avg_mv_max": 2.4},
        "midrange": {"lands": (23, 26), "interaction": (8, 12), "creatures": (14, 24),
                     "card_advantage": (3, 8), "avg_mv_max": 3.0},
        "control":  {"lands": (25, 28), "interaction": (12, 20), "creatures": (2, 10),
                     "card_advantage": (6, 12), "avg_mv_max": 3.4},
        "combo":    {"lands": (20, 24), "interaction": (4, 10), "creatures": (4, 20),
                     "card_advantage": (4, 12), "avg_mv_max": 3.0},
    },
    "limited": {
        "lands": (16, 18), "interaction": (5, 8), "creatures": (13, 17),
        "card_advantage": (1, 5), "avg_mv_max": 3.4,
    },
}


def classify(rec):
    """Roles for one card record (front face text for DFCs is included)."""
    roles = set()
    type_line = (rec.get("type_line") or "")
    front_type = type_line.split("//")[0]
    text = (rec.get("oracle_text") or "").lower()
    if card_is_land(rec):
        roles.add("land")
        return roles
    permanent = any(t in front_type for t in PERMANENT_TYPES)
    if "Creature" in front_type:
        roles.add("creature")
    if permanent and rec.get("produced_mana"):
        roles.add("ramp")
    for role, pats in COMPILED.items():
        if any(p.search(text) for p in pats):
            roles.add(role)
    # "search your library for a basic land ... into your hand" is fixing,
    # not ramp — the ramp regex requires 'onto the battlefield'; landcycling
    # keyword goes to fixing.
    if "landcycling" in text or "basic landcycling" in text:
        roles.add("fixing")
    if "tutor" in roles and "ramp" in roles and "land" in text and "basic land" in text:
        roles.discard("tutor")
    return roles


def load_records(deck_path, enriched_path, cache_path):
    main, side, errors = parse_decklist(deck_path)
    if errors:
        sys.exit(f"ERROR: unparseable decklist lines: {errors}")
    idx = cache_index(load_cache(cache_path))
    en_idx = {}
    if enriched_path:
        enriched = json.loads(Path(enriched_path).read_text(encoding="utf-8-sig"))
        for c in enriched["cards"]:
            if c.get("card"):
                en_idx[norm(c["name"])] = c["card"]
                en_idx[norm(c["card"]["name"])] = c["card"]
    out, missing = [], []
    for entry in main:
        rec = en_idx.get(norm(entry["name"])) or resolve(idx, entry["name"])
        if rec is None and is_basic(entry["name"]):
            rec = synthetic_basic(entry["name"])
        if rec is None:
            missing.append(entry["name"])
            continue
        out.append((entry["count"], rec))
    if missing:
        sys.exit("ERROR: no card data for: " + ", ".join(missing) +
                 " — run card_cache.py validate first (never audit from memory)")
    return out, side


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", required=True)
    ap.add_argument("--enriched", help="enriched.json from card_cache.py validate")
    ap.add_argument("--cache", help="cache path override")
    ap.add_argument("--template", required=True, choices=sorted(TEMPLATES))
    ap.add_argument("--archetype", choices=sorted(TEMPLATES["sixty"]),
                    help="required for --template sixty")
    ap.add_argument("--commander", help="commander name (excluded from the 99 counts, "
                                        "reported separately)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.template == "sixty":
        if not args.archetype:
            sys.exit("ERROR: --template sixty requires --archetype")
        targets = TEMPLATES["sixty"][args.archetype]
    else:
        targets = TEMPLATES[args.template]

    records, side = load_records(args.deck, args.enriched, args.cache)
    commander_norm = norm(args.commander) if args.commander else None

    per_card = []
    counts = {}
    total, lands, mv_sum, nonland_n = 0, 0, 0, 0
    curve = {}
    commander_roles = None
    for count, rec in records:
        roles = classify(rec)
        key = norm(rec["name"])
        front = norm(rec["name"].split(" // ")[0])
        n = count
        if commander_norm and commander_norm in (key, front) and commander_roles is None:
            commander_roles = sorted(roles - {"creature"})
            n -= 1
        per_card.append({"count": count, "name": rec["name"],
                         "mv": int(rec.get("cmc") or 0),
                         "roles": sorted(roles)})
        if n <= 0:
            continue
        total += n
        if "land" in roles:
            lands += n
            continue
        nonland_n += n
        mv = int(rec.get("cmc") or 0)
        mv_sum += mv * n
        curve[mv] = curve.get(mv, 0) + n
        for r in roles:
            counts[r] = counts.get(r, 0) + n

    counts["lands"] = lands
    counts["creatures"] = counts.pop("creature", 0)
    counts["card_advantage"] = counts.get("draw", 0) + counts.get("recursion", 0)
    counts["interaction"] = (counts.get("spot_removal", 0) + counts.get("sweeper", 0)
                             + counts.get("counterspell", 0))
    avg_mv = round(mv_sum / nonland_n, 2) if nonland_n else 0.0
    early = curve.get(1, 0) + curve.get(2, 0)

    findings = []
    for metric, rng in targets.items():
        if metric == "avg_mv_max":
            if avg_mv > rng:
                findings.append(f"avg MV {avg_mv} > {rng} target for this template "
                                "— curve is top-heavy")
            continue
        lo, hi = rng
        v = counts.get(metric, 0)
        if v < lo:
            findings.append(f"{metric}: {v} below target {lo}-{hi}")
        elif v > hi:
            findings.append(f"{metric}: {v} above target {lo}-{hi}")

    result = {
        "deck": args.deck, "template": args.template, "archetype": args.archetype,
        "main_size": total + (1 if commander_roles is not None else 0),
        "sideboard_size": sum(c["count"] for c in side),
        "commander": args.commander if commander_roles is not None else None,
        "commander_roles": commander_roles,
        "counts": {k: counts[k] for k in sorted(counts)},
        "avg_mv_nonland": avg_mv,
        "curve": {str(k): v for k, v in sorted(curve.items())},
        "plays_at_1_2_mv": early,
        "targets": targets,
        "findings": findings,
        "cards": per_card,
    }
    if commander_norm and commander_roles is None:
        result["warnings"] = [f"commander {args.commander!r} not found in the decklist"]

    if args.json:
        print(json.dumps(result, indent=1))
        return
    print(f"Deck audit — template={args.template}"
          f"{' / ' + args.archetype if args.archetype else ''}: "
          f"{result['main_size']} main, {result['sideboard_size']} side, "
          f"avg MV {avg_mv}, {early} plays at 1-2 MV")
    if commander_roles is not None:
        print(f"  commander: {args.commander} (roles: {', '.join(commander_roles) or 'none detected'})")
    print("  package counts (target range):")
    order = ["lands", "ramp", "card_advantage", "draw", "recursion", "tutor",
             "interaction", "spot_removal", "sweeper", "counterspell",
             "protection", "creatures", "token_maker", "lifegain",
             "graveyard_hate", "fixing"]
    for k in order:
        if k in counts or k in targets:
            tgt = targets.get(k)
            tgt_s = f" (target {tgt[0]}-{tgt[1]})" if tgt else ""
            print(f"    {k:16s} {counts.get(k, 0):3d}{tgt_s}")
    print("  curve: " + ", ".join(f"{k}:{v}" for k, v in sorted(curve.items())))
    if findings:
        print("  FINDINGS:")
        for f in findings:
            print(f"    - {f}")
    else:
        print("  all package counts within template ranges")
    if result.get("warnings"):
        for w in result["warnings"]:
            print(f"  warn: {w}")
    print("  per-card roles (override misreads when designing):")
    for c in per_card:
        print(f"    {c['count']:2d} {c['name']:40s} mv{c['mv']} {', '.join(c['roles']) or '-'}")


if __name__ == "__main__":
    main()
