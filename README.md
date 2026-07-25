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
- **Deliverables**: timestamped Moxfield-importable `.txt` decklists and one
  self-contained HTML report (decisions, charts, playtest statistics,
  matchups, iteration log).

## Install

```
/plugin marketplace add <path-or-git-url-of-this-repo>
/plugin install mtg-deckbuilder@mtg-decks
```

Then just ask, e.g. *"Build me two 40-card league decks from my Moxfield
export"* in any project.

> The bundled `MTG_Card_Cache.json` ships pre-warmed. Because plugin
> directories are replaced on update, set the `MTG_CARD_CACHE` environment
> variable to a stable path if you want your growing cache to survive
> plugin updates.

## Requirements

- Python 3.9+ (`python3` on PATH; standard library only)
- Network access to `api.scryfall.com` for cards not yet cached
