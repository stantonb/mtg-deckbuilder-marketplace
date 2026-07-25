#!/usr/bin/env python3
"""Monte Carlo goldfish simulator: opening hands, London mulligans, draws,
land drops and greedy on-curve casting with real colour requirements.

Reports keepable-hand rate, mulligan rate, colour-screw rate by turn,
curve-out probabilities for turns 1-4, average turn the primary win
condition is deployed, and land flood/screw rates — separately on the play
and on the draw. Card data (mana costs, land colours, enters-tapped) comes
from the enriched collection / cache, never from memory.

Definitions used (also echoed in the JSON output):
  keepable hand   7-card hand with 2-5 lands (scaled down after mulligans)
  screwed         < 3 lands in play on turn 3
  flooded         by turn 10, lands drawn >= expected-from-land-ratio + 3
  colour screw    a spell in hand was affordable on raw land count this
                  turn but could not be cast because of coloured pips
  on-curve t      cast at least one spell with mana value == t on turn t
  curve-out t1-4  on-curve on every turn 1..t at which the deck has spells

Lands with an unconditional "enters tapped" cannot pay for spells the turn
they are played; "enters tapped unless..." lands are treated as untapped
(optimistic).

Usage:
  goldfish.py --deck deck.txt --enriched enriched.json \
      [--wincons "Name A;Name B"] [--games 5000] [--seed 7] [--out results.json]
"""
import argparse
import json
import random
import sys
from pathlib import Path

from mtglib import (BASIC_COLORS, cache_index, card_is_land, is_basic,
                    land_etb_tapped, land_produces, load_cache, norm,
                    parse_decklist, parse_mana_cost, resolve, synthetic_basic)

MAX_TURN = 10


def build_sim_deck(deck_path, enriched_path, cache_path, wincon_names):
    main, _side, errors = parse_decklist(deck_path)
    if errors:
        sys.exit(f"ERROR: unparseable decklist lines: {errors}")
    idx = cache_index(load_cache(cache_path))
    enriched = json.loads(Path(enriched_path).read_text(encoding="utf-8-sig")) \
        if enriched_path else {"cards": []}
    en_idx = {}
    for c in enriched["cards"]:
        if c.get("card"):
            en_idx[norm(c["name"])] = c["card"]
            en_idx[norm(c["card"]["name"])] = c["card"]

    wincons = {norm(w) for w in wincon_names}
    cards, missing = [], []
    for entry in main:
        rec = en_idx.get(norm(entry["name"])) or resolve(idx, entry["name"])
        if rec is None and is_basic(entry["name"]):
            rec = synthetic_basic(entry["name"])
        if rec is None:
            missing.append(entry["name"])
            continue
        land = card_is_land(rec)
        generic, pips = parse_mana_cost(rec.get("mana_cost") or "")
        card = {
            "name": rec["name"],
            "is_land": land,
            "produces": land_produces(rec) if land else frozenset(),
            "etb_tapped": land_etb_tapped(rec) if land else False,
            "mv": int(rec.get("cmc") or 0),
            "generic": generic,
            "pips": pips,
            "is_wincon": norm(rec["name"]) in wincons
                         or norm(rec["name"].split(" // ")[0]) in wincons,
        }
        cards.extend([card] * entry["count"])
    if missing:
        sys.exit("ERROR: no card data for: " + ", ".join(missing) +
                 " — run card_cache.py validate first (never simulate from memory)")
    return cards


def try_pay(spell, sources):
    """Greedy pip assignment: most-constrained pip first, least-flexible
    source first. sources = list of frozensets (colours each land can make).
    Returns list of source indexes used, or None."""
    n_needed = len(spell["pips"]) + spell["generic"]
    if n_needed > len(sources):
        return None
    used = [False] * len(sources)
    for pip in sorted(spell["pips"], key=len):
        candidates = [i for i, s in enumerate(sources)
                      if not used[i] and s & pip]
        if not candidates:
            return None
        pick = min(candidates, key=lambda i: len(sources[i]))
        used[pick] = True
    free = [i for i, u in enumerate(used) if not u]
    if spell["generic"] > len(free):
        return None
    return [i for i, u in enumerate(used) if u] + free[:spell["generic"]]


def keep_rule(hand, hand_size):
    lands = sum(1 for c in hand if c["is_land"])
    if hand_size >= 6:
        return 2 <= lands <= 5
    if hand_size == 5:
        return 1 <= lands <= 4
    return True


def bottom_cards(hand, n, target_lands):
    """London mulligan: choose n cards to bottom, steering toward
    target_lands lands and keeping the cheapest spells."""
    hand = list(hand)
    for _ in range(n):
        lands = sum(1 for c in hand if c["is_land"])
        spells = sorted((c for c in hand if not c["is_land"]),
                        key=lambda c: -c["mv"])
        if lands > target_lands or not spells:
            victim = next(c for c in hand if c["is_land"])
        else:
            victim = spells[0]
        hand.remove(victim)
    return hand


def simulate(deck, games, on_play, seed):
    land_count = sum(1 for c in deck if c["is_land"])
    ratio = land_count / len(deck)
    mv_present = {c["mv"] for c in deck if not c["is_land"]}
    st = {
        "games": games, "keepable": 0, "mulliganed": 0, "hand_sizes": [],
        "screwed_t3": 0, "flooded_t10": 0,
        "missed_drop": {t: 0 for t in range(1, 6)},
        "color_screw": {t: 0 for t in range(1, 6)},
        "on_curve": {t: 0 for t in range(1, 5)},
        "curve_out": {t: 0 for t in range(1, 5)},
        "wincon_turns": [], "wincon_by_t10": 0,
        "mana_spent_t5": [],
    }
    rng = random.Random(seed)
    for g in range(games):
        library = deck[:]
        rng.shuffle(library)
        hand = library[:7]
        library = library[7:]
        if keep_rule(hand, 7):
            st["keepable"] += 1
            kept = 7
        else:
            st["mulliganed"] += 1
            kept = 7
            while kept > 4:
                kept -= 1
                library = deck[:]
                rng.shuffle(library)
                hand = library[:7]
                library = library[7:]
                if keep_rule(hand, kept) or kept == 4:
                    hand = bottom_cards(hand, 7 - kept,
                                        max(2, round(kept * ratio)))
                    break
        st["hand_sizes"].append(kept)

        battlefield = []          # (produces, entered_this_turn_tapped)
        lands_drawn = sum(1 for c in hand if c["is_land"])
        cards_seen = len(hand)
        mana_spent = 0
        wincon_turn = None
        curve_ok = True
        for turn in range(1, MAX_TURN + 1):
            if not (turn == 1 and on_play):
                if library:
                    drawn = library.pop(0)
                    hand.append(drawn)
                    cards_seen += 1
                    if drawn["is_land"]:
                        lands_drawn += 1
            # play a land: prefer one adding a colour the hand needs, untapped
            lands_in_hand = [c for c in hand if c["is_land"]]
            if lands_in_hand:
                needed = set()
                for c in hand:
                    for pip in c.get("pips", []):
                        needed |= pip
                have = set()
                for prod, _ in battlefield:
                    have |= prod
                def score(l):
                    return (len(l["produces"] & (needed - have)),
                            not l["etb_tapped"], len(l["produces"]))
                land = max(lands_in_hand, key=score)
                hand.remove(land)
                battlefield.append((land["produces"], land["etb_tapped"]))
            else:
                if turn <= 5:
                    st["missed_drop"][turn] += 1

            usable = [prod for prod, tapped_now in battlefield if not tapped_now]
            if turn <= 3 and len(battlefield) < min(turn, 3) and turn == 3:
                st["screwed_t3"] += 1

            # colour-screw check before casting
            if turn <= 5:
                for c in hand:
                    if not c["is_land"] and c["mv"] <= len(usable):
                        if try_pay(c, usable) is None:
                            st["color_screw"][turn] += 1
                            break

            # greedy casting, most expensive castable first
            cast_mvs = []
            while True:
                castable = None
                for c in sorted((c for c in hand if not c["is_land"]),
                                key=lambda c: -c["mv"]):
                    pay = try_pay(c, usable)
                    if pay is not None:
                        castable = (c, pay)
                        break
                if castable is None:
                    break
                c, pay = castable
                for i in sorted(pay, reverse=True):
                    usable.pop(i)
                hand.remove(c)
                cast_mvs.append(c["mv"])
                mana_spent += c["mv"]
                if c["is_wincon"] and wincon_turn is None:
                    wincon_turn = turn

            if turn <= 4:
                if turn in mv_present and turn in cast_mvs:
                    st["on_curve"][turn] += 1
                elif turn in mv_present:
                    curve_ok = False
                if curve_ok:
                    st["curve_out"][turn] += 1
            if turn == 5:
                st["mana_spent_t5"].append(mana_spent)
            if turn == MAX_TURN:
                expected = ratio * cards_seen
                if lands_drawn >= expected + 3:
                    st["flooded_t10"] += 1
            # untap: everything usable next turn
            battlefield = [(prod, False) for prod, _ in battlefield]
        if wincon_turn is not None:
            st["wincon_turns"].append(wincon_turn)
            st["wincon_by_t10"] += 1
    return st, land_count, mv_present


def summarize(st, games):
    pct = lambda n: round(100 * n / games, 1)
    out = {
        "keepable_hand_rate_pct": pct(st["keepable"]),
        "mulligan_rate_pct": pct(st["mulliganed"]),
        "avg_kept_hand_size": round(sum(st["hand_sizes"]) / games, 2),
        "screw_rate_pct_lt3_lands_t3": pct(st["screwed_t3"]),
        "flood_rate_pct_by_t10": pct(st["flooded_t10"]),
        "missed_land_drop_pct_by_turn": {t: pct(v) for t, v in st["missed_drop"].items()},
        "color_screw_pct_by_turn": {t: pct(v) for t, v in st["color_screw"].items()},
        "on_curve_pct_by_turn": {t: pct(v) for t, v in st["on_curve"].items()},
        "curved_out_through_turn_pct": {t: pct(v) for t, v in st["curve_out"].items()},
        "avg_mana_spent_by_t5": round(sum(st["mana_spent_t5"]) / games, 2),
    }
    if st["wincon_turns"]:
        out["wincon_avg_first_cast_turn"] = round(
            sum(st["wincon_turns"]) / len(st["wincon_turns"]), 2)
        out["wincon_cast_by_t10_pct"] = pct(st["wincon_by_t10"])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", required=True)
    ap.add_argument("--enriched", help="enriched.json (recommended)")
    ap.add_argument("--cache", help="cache path override")
    ap.add_argument("--wincons", default="",
                    help="';'-separated primary win-condition card names")
    ap.add_argument("--games", type=int, default=5000,
                    help="games per side (play/draw); default 5000")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", help="write results JSON here")
    args = ap.parse_args()

    wincons = [w for w in args.wincons.split(";") if w.strip()]
    deck = build_sim_deck(args.deck, args.enriched, args.cache, wincons)
    lands = sum(1 for c in deck if c["is_land"])
    nonlands = [c for c in deck if not c["is_land"]]
    curve = {}
    for c in nonlands:
        curve[c["mv"]] = curve.get(c["mv"], 0) + 1
    pip_counts = {}
    for c in nonlands:
        for pip in c["pips"]:
            for col in pip:
                pip_counts[col] = pip_counts.get(col, 0) + 1 / len(pip)
    pip_counts = {k: round(v, 1) for k, v in sorted(pip_counts.items())}

    results = {"deck": args.deck, "deck_size": len(deck), "lands": lands,
               "games_per_side": args.games, "seed": args.seed,
               "wincons": wincons,
               "avg_mv_nonland": round(sum(c["mv"] for c in nonlands) / len(nonlands), 2),
               "curve": {str(k): v for k, v in sorted(curve.items())},
               "colored_pip_counts": pip_counts,
               "definitions": {
                   "screwed": "<3 lands in play on turn 3",
                   "flooded": "lands drawn >= land-ratio expectation + 3 by turn 10",
                   "color_screw": "spell affordable on land count but not on colours that turn",
                   "on_curve": "cast a spell with mv==t on turn t (turns where deck has that mv)",
               }}
    for label, on_play in (("play", True), ("draw", False)):
        st, _, _ = simulate(deck, args.games, on_play, args.seed + (0 if on_play else 1))
        results[label] = summarize(st, args.games)

    out = json.dumps(results, indent=1)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
