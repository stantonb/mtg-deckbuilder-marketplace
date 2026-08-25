# mtg-decks — Claude Code plugin marketplace

A plugin marketplace for Magic: The Gathering deckbuilding with
[Claude Code](https://claude.com/claude-code).

## Plugins

### mtg-deckbuilder

Three skills that build professional-quality MTG decks **using only cards
you own**, playtest them, and deliver Moxfield-ready decklists plus a
self-contained HTML report. Pick the skill by format — Claude does this from
your request automatically:

| Skill | Format | Method reference |
|---|---|---|
| `mtg-deckbuilder` | 40-card Limited: league, sealed, draft, set-restricted pools | Draftsim-style limited build (17 lands / 23 spells, pool scoring) |
| `mtg-deckbuilder-60` | 60-card constructed: Standard, Modern, Pioneer, Legacy, Pauper, kitchen table | "The minimum is the maximum": exactly 60, 24-land skeleton, four-of philosophy, bell curve, Karsten source math, 15-card sideboard guide |
| `mtg-commander` | Commander / EDH (99 + commander, singleton) | Package construction (1 + 35-38 lands + eight ~8-card packages), pip-share mana base, bracket 1-5 self-assessment, four-player pod playtests |

Shared across all three:

- **Collection-aware**: parses Moxfield / Archidekt / Deckbox / ManaBox CSV
  exports (plus a generic fallback), aggregating duplicates and printings.
- **Card truth from Scryfall, never from memory**: every card is validated
  against the Scryfall API (batched, rate-limited) and cached in
  `MTG_Card_Cache.json`; cache hits are trusted and never re-fetched. Failed
  lookups get fuzzy-match suggestions — never guessed, never dropped.
- **Format-aware quality gates**: deck size, copy limits, format legality,
  commander colour identity, set restrictions, ownership counts, and a ledger
  for multi-deck builds that must share one pool ("simultaneous" policy).
- **Role audit**: counts lands / ramp / card advantage / removal / sweepers /
  creatures from verified oracle text against per-format target ranges.
- **Playtesting**: a Monte Carlo goldfish simulator (opening hands, London
  mulligans, colour-aware casting, enters-tapped lands, mana rocks and
  land-fetch ramp, command zone, play/draw) plus narrated sample games.
- **Deliverables**: each run creates a `<Run Name> Deck Build <timestamp>/`
  folder in your project directory containing timestamped Moxfield-importable
  `.txt` decklists and one self-contained HTML report (decisions, charts,
  playtest statistics, matchups, iteration log, plus format-specific sections
  such as the sideboard guide or the Commander package table).

## Install

```
/plugin marketplace add stantonb/mtg-deckbuilder-marketplace
/plugin install mtg-deckbuilder@mtg-decks
```

Then just ask, e.g. *"Build me two 40-card league decks from my Moxfield
export"*, *"Make a Standard deck with a sideboard from my collection"*, or
*"Which commander do my cards support best? Build it for a bracket-2 pod"*.

> The bundled `MTG_Card_Cache.json` ships pre-warmed and lives in the
> `mtg-deckbuilder` skill directory (all three skills share it). Because
> plugin directories are replaced on update, set the `MTG_CARD_CACHE`
> environment variable to a stable path if you want your growing cache to
> survive plugin updates.

## Parameters

Each skill collects these when you ask for decks (it will prompt for anything
required that you didn't mention).

### Common to all skills

| Parameter | Required? | Default | Accepted values / notes |
|-----------|-----------|---------|-------------------------|
| **Collection CSV path** | required | — | Moxfield "haves" export works out of the box; Archidekt, Deckbox and ManaBox are auto-detected by header; any CSV with name + count columns falls back to generic parsing |
| **Restrictions** | optional | none | Freeform: "only cards from set X", "no rares", "two colours max", "must include card Y", custom ban list |
| **Number of decks** | optional | 1 | When > 1, decks are built as genuinely distinct archetypes |
| **Overlap policy** | required when N > 1 | — | `shared pool` (decks are alternatives; may reuse the same physical copies) or `simultaneous` (all decks buildable at once; a ledger guarantees no card is used more times than owned) |
| **Preferences** | optional | none | Archetype / colours / theme; power target; `suggest-upgrades` flag (off by default — when on, lists the best cards *not* in your collection with cached prices) |

### `mtg-deckbuilder` (40-card limited)

| Parameter | Required? | Default | Notes |
|-----------|-----------|---------|-------|
| **Format** | required | — | `limited` (aliases `league`, `sealed`, `draft`) |
| **Deck size override** | optional | 40 | e.g. a 40-card league deck with 17 lands |
| **Set restriction** | optional | none | "only cards from set X" → every nonbasic must be owned in that set |

### `mtg-deckbuilder-60` (60-card constructed)

| Parameter | Required? | Default | Notes |
|-----------|-----------|---------|-------|
| **Format** | required | — | `standard`, `modern`, `pioneer`, `legacy`, `pauper`, `kitchen` (casual — no legality gate; house rules via copy-limit/ban overrides). Legality comes from the cached Scryfall data |
| **Sideboard** | optional | 15 for sanctioned formats, none for kitchen | Each sideboard card names the matchup it comes in for and what leaves |
| **Expected metagame** | optional | six standard archetypes | What the deck must beat; drives sideboard and matchup sections |
| **Archetype** | optional | pool decides | aggro / midrange / control / combo — the audit targets and playtest thresholds follow it |

Decks are always exactly 60 cards.

### `mtg-commander` (Commander / EDH)

| Parameter | Required? | Default | Notes |
|-----------|-----------|---------|-------|
| **Commander** | optional | chosen from your pool | An owned legendary creature (or "can be your commander" card). Say "help me choose" to get a scored shortlist of owned candidates |
| **Theme / plan** | optional | from the commander's text | e.g. spellslinger, tokens, aristocrats |
| **Bracket target** | optional | 3 | 1-5. Bracket ≤ 2 also means: no Game Changers, no 2-card infinite combos, no mass land denial, no extra-turn chaining — supply the current Game Changers list (it is never recalled from memory) |
| **Playgroup notes** | optional | none | What the table enjoys or hates |

Decks are always exactly 100 cards, singleton, inside the commander's colour
identity.

## Script reference (advanced / direct use)

All three skills drive five stdlib-only Python scripts in
`plugins/mtg-deckbuilder/skills/mtg-deckbuilder/scripts/`. They also work
standalone; every script supports `--help`.

### `parse_collection.py <collection.csv> [--out collection.json]`

CSV → normalised collection JSON (layout auto-detection, duplicate/printing
aggregation, warnings for proxies and odd rows).

### `card_cache.py [--cache PATH] <command>`

| Command | Flags | Purpose |
|---------|-------|---------|
| `validate` | `--collection collection.json`, `--out enriched.json`, `--no-fetch` | Cache-first validation of the whole collection; misses fetched from Scryfall in batches of 75; exit code 2 + fuzzy suggestions when a name can't be resolved |
| `lookup` | `<names...>`, `--no-fetch` | Ad-hoc lookups (e.g. upgrade candidates) |
| `stats` | — | Cache size / path / last-updated |

`--cache` (or the `MTG_CARD_CACHE` env var) relocates the cache file.

### `validate_deck.py --deck deck.txt --enriched enriched.json --format FMT [...]`

| Flag | Purpose |
|------|---------|
| `--format` | `commander`/`edh`, `standard`, `modern`, `pioneer`, `legacy`, `pauper`, `limited` (`league`, `sealed`, `draft`), `kitchen` (`casual`) |
| `--deck-size N` | Exact main-deck size override (the 60-card skill always passes 60) |
| `--max-copies N` | Copy-limit override (kitchen-table house rules) |
| `--commander "Name"` | Commander: enforces colour identity + presence in list |
| `--restrict-set CODE` | Every nonbasic must be owned in this set (league pools) |
| `--ban "A;B"` / `--require "C;D"` | Custom ban list (e.g. Game Changers for bracket ≤ 2) / must-includes |
| `--ledger ledger.json` | Simultaneous overlap policy: charges copies across decks |
| `--export-dir DIR --deck-name "Name"` | On pass, writes the timestamped Moxfield `.txt` |
| `--json` | Machine-readable result |

Exit 0 = all gates pass; exit 1 = failures listed. Basic lands are always
exempt from ownership/copy checks.

### `deck_audit.py --deck deck.txt --enriched enriched.json --template T [...]`

| Flag | Purpose |
|------|---------|
| `--template` | `commander`, `sixty`, or `limited` — selects the target ranges |
| `--archetype` | `aggro` / `midrange` / `control` / `combo` (required with `sixty`) |
| `--commander "Name"` | Excludes the commander from the 99 counts and reports its roles separately |
| `--json` | Machine-readable result |

Advisory (always exit 0 on valid input): classifies every card's roles —
ramp, draw, recursion, tutor, spot removal, sweeper, counterspell,
protection, token maker, lifegain, graveyard hate, fixing — from cached
oracle text and `produced_mana`, prints package counts against the
template's ranges, the curve, average MV and a FINDINGS list. The
classification is keyword-based, so the per-card role table is printed for
the deckbuilder to override.

### `goldfish.py --deck deck.txt --enriched enriched.json [...]`

| Flag | Default | Purpose |
|------|---------|---------|
| `--wincons "A;B"` | none | Primary win-condition cards (enables deploy-turn metrics) |
| `--commander "Name"` | none | Commander mode: one copy moves to the command zone (library = 99), castable any turn, no tax; reports `commander_avg_cast_turn` |
| `--games N` | 5000 | Games per side (runs both play and draw) |
| `--seed N` | 7 | Reproducible shuffles |
| `--out results.json` | stdout | Full metrics JSON |

Reports keepable-hand %, mulligan %, missed land drops, colour screw by
turn, curve-out probabilities (turns 1–4), flood/screw rates, average mana
sources on turn 4, ramp deployed by turn 3, average win-condition deploy
turn, and the deck's curve/pip/type stats. Ramp is modelled: nonland
permanents with a Scryfall `produced_mana` value (rocks, dorks) become
mana sources the turn after they are cast, and spells that put a land onto
the battlefield pull a basic from the library, tapped. One-shot mana and
cost reducers are not modelled.

## Requirements

- Python 3.9+ (`python3` on PATH; standard library only)
- Network access to `api.scryfall.com` for cards not yet cached
