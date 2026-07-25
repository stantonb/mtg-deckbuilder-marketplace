---
name: mtg-deckbuilder
description: "Use when the user wants Magic: The Gathering decks built, rebuilt, evaluated or playtested from cards they own — 'build me a deck', 'make N decks from my collection', 'deckbuild from this CSV', a Moxfield/Archidekt/Deckbox/ManaBox export, sealed/league pool, Commander/Standard/Modern/Pauper brews, goldfish or playtest requests, deck reports, or checking decklists against a collection. Use it even for quick deck questions if a collection file is in play."
---

# MTG Deckbuilder

Builds professional-quality Magic: The Gathering decks **using only cards the
user owns**, playtests them with a Monte Carlo simulator plus narrated games,
and delivers Moxfield-ready decklists and a self-contained HTML report.

Scripts live in `scripts/` (run with `python3`, stdlib only, work from any
directory). The card cache `MTG_Card_Cache.json` lives in THIS skill
directory and is shared by every project (set the `MTG_CARD_CACHE` env var
to relocate it — e.g. when installed as a plugin, whose directory is
replaced on updates). Set once at the start:

```bash
SKILL="<this skill's base directory — shown when the skill loads>"
WORK=$(mktemp -d)   # intermediates; final outputs go in the project dir
```

## Two iron rules

1. **Card truth comes from the cache, never from memory.** Cache hit →
   trust every field as-is, do not re-fetch. Miss → `card_cache.py`
   validates via Scryfall (batched, rate-limited). Sets released after the
   knowledge cutoff make remembered card text wrong — if you catch yourself
   typing oracle text you didn't read from the cache, stop and look it up.
   A failed lookup is reported to the user with the fuzzy suggestions the
   script prints — never guess, never silently drop a card.
2. **Every deck passes `validate_deck.py` before the user sees it.** No
   exceptions for "obviously fine" decks — the gates catch ownership
   overruns, illegal cards, and size errors that eyeballing misses.

## Step 0 — Gather inputs

Ask for whatever is missing (defaults in parentheses):

1. Collection CSV path (required)
2. Format (required): commander/standard/modern/pioneer/legacy/pauper/
   limited (league, sealed)/kitchen table — see `references/formats.md`
3. Deck size override (format default)
4. Restrictions, freeform (none): set-only, rarity caps, color caps,
   must-includes, ban list
5. Number of decks (1)
6. Overlap policy when N > 1 (must ask): **shared pool** or **simultaneous**
7. Preferences (none): archetype/colors/theme, power target,
   suggest-upgrades flag (off)

## Step 1 — Parse and validate the collection

```bash
python3 $SKILL/scripts/parse_collection.py "<collection.csv>" --out $WORK/collection.json
python3 $SKILL/scripts/card_cache.py validate --collection $WORK/collection.json --out $WORK/enriched.json
```

Auto-detects Moxfield/Archidekt/Deckbox/ManaBox layouts; aggregates
duplicates and printings. `validate` exits 2 if any card failed — report
those to the user with the printed suggestions and get corrections before
building. Read `$WORK/enriched.json` for real oracle text while designing
(it is large — read selectively, e.g. filter with python, not the whole file).

## Step 2 — Design the deck(s)

Read `references/deckbuilding-method.md` and follow its 11 steps: score the
pool per color pair FIRST, then archetype → colors → curve → mana base →
interaction → card advantage → wincons → synergy pass. Record every
decision and near-miss cut as you go — the report needs them. For N > 1,
decks must be genuinely distinct archetypes.

Write each candidate as a plain decklist: `N Card Name` lines, optional
`Sideboard` section. Save as `$WORK/deck1.txt` etc.

## Step 3 — Quality gates

```bash
python3 $SKILL/scripts/validate_deck.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --format limited --deck-size 40 \
  --restrict-set ecl   # plus --ban/--require/--commander as applicable
```

Simultaneous overlap policy: add `--ledger $WORK/ledger.json` to EVERY
deck's validate call, and export decks in build order (the ledger charges
copies on export). Shared pool: no ledger. Fix every FAIL and re-run until
clean — do not rationalize a failure away.

## Step 4 — Playtest (both parts required)

```bash
python3 $SKILL/scripts/goldfish.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --wincons "Card A;Card B" \
  --games 5000 --out $WORK/deck1-goldfish.json
```

Then narrate 2-3 short sample games per deck (one paragraph + lesson each),
at least one against a hostile scenario (aggro rush, board wipe). Use only
cache-verified card behavior in the narration.

## Step 5 — Iterate

Compare the numbers against the thresholds in
`references/deckbuilding-method.md` §11. Adjust, re-validate (Step 3),
re-simulate (Step 4). Keep a short changelog — the report has an iteration
section. First builds that survive untouched are rare; say why if so.

## Step 6 — Deliver

1. **Decklists**: re-run each final deck's `validate_deck.py` with
   `--export-dir "<project dir>" --deck-name "<Deck Name>"` (and the ledger
   if simultaneous). This writes the timestamped Moxfield-importable
   `.txt` (`N Card Name (SET) collector-number`). Also show each list in
   chat in the same format.
2. **HTML report**: one self-contained file per run following
   `references/report-spec.md` exactly — decisions, near-miss cuts, charts,
   full goldfish numbers, sample-game lessons, matchup grid vs the six
   standard archetypes, iteration log, and (N > 1) ranked comparison +
   overlap. Every number traces to a script output.
3. If suggest-upgrades was requested: validate candidates through
   `card_cache.py lookup` and use the cached price snapshot.

## Final checklist before showing output

- [ ] validate_deck.py PASS for every deck (with ledger if simultaneous)
- [ ] Zero cards included on remembered stats (all cache-verified)
- [ ] goldfish.py ran; its numbers appear in the report
- [ ] Sample games narrated (incl. one hostile)
- [ ] Land count/curve match method targets or the report explains why not
- [ ] Decklist .txt files exported (timestamped) + shown in chat
- [ ] Report is one file, opens offline, all sections present

## Troubleshooting

| Symptom | Fix |
|---|---|
| `validate` exit 2 / "not found on Scryfall" | Typo or wrong name — show the user the suggestions; never guess |
| Scryfall 429s | The script backs off automatically; just rerun if it aborted |
| Double-faced card not matching | Use the full "Front // Back" name or just the front face — both resolve |
| Unknown CSV layout | parse_collection falls back to generic name/count detection; check its warnings |
| Deck uses a card twice across decks (simultaneous) | Expected: the ledger blocks it — pick a substitute |
| Basics rejected | They never should be — basics are exempt; check the name is a real basic |
