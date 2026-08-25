---
name: mtg-deckbuilder-60
description: "Use whenever the user wants a 60-card constructed Magic: The Gathering deck — Standard, Modern, Pioneer, Legacy, Pauper, or casual/kitchen-table 60 — built, rebuilt, tuned, sideboarded, evaluated or playtested from cards they own. Trigger on 'build me a Standard deck from my Moxfield export', 'make a 60-card mono-red list', 'tune my Modern deck', 'what sideboard should I run', 'is my Pioneer list legal', or any mention of a 60-card deck, a sideboard, 4-ofs, or a constructed format together with a collection CSV, even if the word deck isn't used. Not for 40-card limited (mtg-deckbuilder) or Commander (mtg-commander)."
---

# MTG Deckbuilder — 60-card constructed

Builds tournament-shaped 60-card decks **using only cards the user owns**,
following the 60-card method in `references/sixty-card-method.md`,
playtests them, and delivers Moxfield-ready decklists plus a
self-contained HTML report.

This skill shares its toolkit with the sibling `mtg-deckbuilder` skill
(40-card limited): the scripts, the card cache and the generic method,
format and report references all live there. Set once at the start:

```bash
SKILL="<this skill's base directory — shown when the skill loads>"
CORE="$SKILL/../mtg-deckbuilder"          # shared scripts + cache + references
WORK=$(mktemp -d)                          # intermediates only — never shown to the user
OUT="<project dir>/<Run Name> Deck Build $(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"                            # ALL final deliverables go here
```

Scripts: `python3 $CORE/scripts/<name>.py` (stdlib only, work from any
directory). The card cache is `$CORE/MTG_Card_Cache.json` unless the
`MTG_CARD_CACHE` env var relocates it.

## Two iron rules (same as the core skill)

1. **Card truth comes from the cache, never from memory.** Cache hit →
   trust it. Miss → `card_cache.py` fetches from Scryfall. Post-cutoff
   sets and recent bannings make remembered card text and legality wrong.
   A failed lookup is shown to the user with the printed fuzzy
   suggestions — never guessed, never dropped.
2. **Every deck passes `validate_deck.py` before the user sees it** —
   always with `--deck-size 60`. "The minimum is the maximum": a 61st
   card is never justified by "it's just one more".

## Step 0 — Gather inputs

Ask for whatever is missing (defaults in parentheses):

1. Collection CSV path (required)
2. Format (required): `standard`, `modern`, `pioneer`, `legacy`,
   `pauper`, or `kitchen` (casual — no legality check, house rules via
   `--max-copies`/`--ban`). Legality comes from the cache's `legalities`.
3. Archetype / colors / theme (let the pool decide — see method §1)
4. Sideboard wanted? (yes for sanctioned formats — 15 cards; no for kitchen
   table unless asked)
5. Expected metagame / what the deck must beat (none — assume the six
   standard archetypes)
6. Restrictions, freeform (none): budget of owned copies, ban list,
   must-includes, colour caps
7. Number of decks (1) and, when N > 1, overlap policy (**must ask**):
   `shared pool` or `simultaneous`
8. Power target (competitive for sanctioned formats, casual for kitchen)
   and `suggest-upgrades` flag (off)

## Step 1 — Parse and validate the collection

```bash
python3 $CORE/scripts/parse_collection.py "<collection.csv>" --out $WORK/collection.json
python3 $CORE/scripts/card_cache.py validate --collection $WORK/collection.json --out $WORK/enriched.json
```

`validate` exits 2 if any card failed — report those with the suggestions
and get corrections before building. Read `$WORK/enriched.json`
selectively (filter with python; it is large). Useful first filter for
constructed: keep only cards whose `legalities[<format>]` is `legal` and
count owned copies — a 4-of plan needs 4 owned copies (basics excepted).

## Step 2 — Design

Follow `references/sixty-card-method.md` in order: pool scoring → archetype
→ colours → the 24/24-28/8-12 skeleton adjusted for archetype → four-of
philosophy → bell-curve check → mana base math → interaction/card
advantage/wincon minimums → sideboard. The generic steps (pool scoring,
synergy pass, narrated games) are in `$CORE/references/deckbuilding-method.md`;
the format table is `$CORE/references/formats.md`.

Record every decision and every near-miss cut as you go — the report needs
them, including the reason for each card's copy count.

Write each candidate as `N Card Name` lines with an optional `Sideboard`
section, saved as `$WORK/deck1.txt` etc.

## Step 3 — Quality gates (both required)

```bash
python3 $CORE/scripts/validate_deck.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --format standard --deck-size 60
python3 $CORE/scripts/deck_audit.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --template sixty --archetype midrange
```

`validate_deck.py` enforces size, 4-copy limit, legality, ownership and the
sideboard cap (exit 1 on any FAIL — fix and re-run, never rationalise).
`deck_audit.py` is advisory: it counts lands / interaction / card advantage
/ creatures against the archetype's target ranges and prints each card's
detected roles — override a misread in your head, but explain any range you
deliberately leave in the report. Simultaneous overlap policy: add
`--ledger $WORK/ledger.json` to EVERY validate call and export in build
order.

## Step 4 — Playtest (both parts required)

```bash
python3 $CORE/scripts/goldfish.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --wincons "Card A;Card B" \
  --games 5000 --out $WORK/deck1-goldfish.json
```

Then narrate 2-3 short sample games per deck (one paragraph + lesson
each): at least one on the draw against a faster deck, and one against a
sweeper or heavy removal. Use only cache-verified card behaviour. For decks
with a sideboard, one narrated game should be post-sideboard (state the
swaps).

## Step 5 — Iterate

Compare against the 60-card thresholds in `references/sixty-card-method.md`
§10. Adjust, re-validate, re-audit, re-simulate. Keep a changelog — the
report has an iteration section. Zero iterations is suspicious; say why.

## Step 6 — Deliver

1. **Decklists**: re-run each final deck's `validate_deck.py` with
   `--export-dir "$OUT" --deck-name "<Deck Name>"` (plus the ledger if
   simultaneous). Sideboard is written under a `Sideboard:` header in the
   same Moxfield-importable file. Also show each list in chat.
2. **HTML report**: one self-contained file in `$OUT` following
   `$CORE/references/report-spec.md` **plus** the 60-card sections in
   `references/report-addendum.md` (copy-count rationale, land math,
   sideboard guide, legality statement). Every number traces to a script.
3. If suggest-upgrades was requested: validate candidates through
   `card_cache.py lookup` and use the cached price snapshot.

## Final checklist before showing output

- [ ] validate_deck.py PASS with `--deck-size 60` for every deck (ledger if simultaneous)
- [ ] Sideboard is exactly 15 (or explicitly none for kitchen table)
- [ ] deck_audit.py run; every out-of-range count either fixed or justified
- [ ] Every card cache-verified and legal in the format per the cache
- [ ] Copy counts justified (4-of core, fewer only for a stated reason)
- [ ] goldfish.py ran; numbers in the report; thresholds checked
- [ ] Sample games narrated (incl. one on the draw vs. faster deck, one vs. sweeper)
- [ ] Decklist .txt exported (timestamped) + shown in chat
- [ ] Report is one file, opens offline, all sections incl. sideboard guide
- [ ] Everything inside `$OUT`; user told the path

## Troubleshooting

| Symptom | Fix |
|---|---|
| `validate` exit 2 / "not found on Scryfall" | Typo or wrong name — show the user the suggestions; never guess |
| `X: not_legal in standard` | The cache says so — it rotated or was banned; pick another card, don't argue with the cache |
| Only 2-3 owned copies of a core card | Run what is owned, note the shortfall in the report; suggest-upgrades lists the missing copies |
| `sideboard 16 > allowed 15` | Cut to 15 — the gate is the rule |
| deck_audit misreads a card's role | Roles are keyword heuristics; override in the report with the oracle text quoted |
| Deck uses a card twice across decks (simultaneous) | Expected — the ledger blocks it; substitute |
