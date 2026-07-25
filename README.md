# mtg-decks — Claude Code plugin marketplace

A plugin marketplace for Magic: The Gathering deckbuilding with
[Claude Code](https://claude.com/claude-code).

## Plugins

### mtg-deckbuilder

Builds professional-quality MTG decks **using only cards you own**, playtests
them, and delivers Moxfield-ready decklists plus a self-contained HTML report.

- **Collection-aware**: parses Moxfield / Archidekt / Deckbox / ManaBox CSV
  exports (plus a generic fallback), aggregating duplicates and printings.
- **Card truth from Scryfall, never from memory**: every card is validated
  against the Scryfall API (batched, rate-limited) and cached in
  `MTG_Card_Cache.json`; cache hits are trusted and never re-fetched. Failed
  lookups get fuzzy-match suggestions — never guessed, never dropped.
- **Format-aware quality gates**: deck size, copy limits, format legality,
  commander color identity, set restrictions, ownership counts, and a ledger
  for multi-deck builds that must share one pool ("simultaneous" policy).
- **Playtesting**: a Monte Carlo goldfish simulator (opening hands, London
  mulligans, color-aware casting, enters-tapped lands, play/draw) plus
  narrated sample games.
- **Deliverables**: each run creates a `<Run Name> Deck Build <timestamp>/`
  folder in your project directory containing timestamped Moxfield-importable
  `.txt` decklists and one self-contained HTML report (decisions, charts,
  playtest statistics, matchups, iteration log).

## Install

```
/plugin marketplace add stantonb/mtg-deckbuilder-marketplace
/plugin install mtg-deckbuilder@mtg-decks
```

Then just ask, e.g. *"Build me two 40-card league decks from my Moxfield
export"* in any project.

> The bundled `MTG_Card_Cache.json` ships pre-warmed. Because plugin
> directories are replaced on update, set the `MTG_CARD_CACHE` environment
> variable to a stable path if you want your growing cache to survive
> plugin updates.

## Parameters

The skill collects these when you ask for decks (it will prompt for anything
required that you didn't mention):

| # | Parameter | Required? | Default | Accepted values / notes |
|---|-----------|-----------|---------|-------------------------|
| 1 | **Collection CSV path** | required | — | Moxfield "haves" export works out of the box; Archidekt, Deckbox and ManaBox are auto-detected by header; any CSV with name + count columns falls back to generic parsing |
| 2 | **Format** | required | — | `commander`/`edh`, `standard`, `modern`, `pioneer`, `legacy`, `pauper`, `limited` (`league`, `sealed`, `draft`), `kitchen table` (`casual`). Sets deck size, copy limits, singleton rules, commander color identity and per-card legality automatically |
| 3 | **Deck size override** | optional | format default | e.g. a 40-card league deck with 17 lands; overrides the format's size rule |
| 4 | **Restrictions** | optional | none | Freeform: "only cards from set X", "no rares", "two colors max", "must include card Y", custom ban list |
| 5 | **Number of decks** | optional | 1 | When > 1, decks are built as genuinely distinct archetypes |
| 6 | **Overlap policy** | required when N > 1 | — | `shared pool` (decks are alternatives; may reuse the same physical copies) or `simultaneous` (all decks buildable at once; a ledger guarantees no card is used more times than owned) |
| 7 | **Preferences** | optional | none | Archetype / colors / theme; power target (casual ↔ competitive); `suggest-upgrades` flag (off by default — when on, lists the best cards *not* in your collection with cached prices) |

## Script reference (advanced / direct use)

The skill drives four stdlib-only Python scripts in `skills/mtg-deckbuilder/scripts/`.
They also work standalone; every script supports `--help`.

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
| `--format` | One of the formats above (aliases accepted) |
| `--deck-size N` | Exact main-deck size override |
| `--max-copies N` | Copy-limit override (kitchen-table house rules) |
| `--commander "Name"` | Commander: enforces color identity + presence in list |
| `--restrict-set CODE` | Every nonbasic must be owned in this set (league pools) |
| `--ban "A;B"` / `--require "C;D"` | Custom ban list / must-includes |
| `--ledger ledger.json` | Simultaneous overlap policy: charges copies across decks |
| `--export-dir DIR --deck-name "Name"` | On pass, writes the timestamped Moxfield `.txt` |
| `--json` | Machine-readable result |

Exit 0 = all gates pass; exit 1 = failures listed. Basic lands are always
exempt from ownership/copy checks.

### `goldfish.py --deck deck.txt --enriched enriched.json [...]`

| Flag | Default | Purpose |
|------|---------|---------|
| `--wincons "A;B"` | none | Primary win-condition cards (enables deploy-turn metrics) |
| `--games N` | 5000 | Games per side (runs both play and draw) |
| `--seed N` | 7 | Reproducible shuffles |
| `--out results.json` | stdout | Full metrics JSON |

Reports keepable-hand %, mulligan %, missed land drops, colour screw by
turn, curve-out probabilities (turns 1–4), flood/screw rates, average
win-condition deploy turn, and the deck's curve/pip/type stats.

## Requirements

- Python 3.9+ (`python3` on PATH; standard library only)
- Network access to `api.scryfall.com` for cards not yet cached
