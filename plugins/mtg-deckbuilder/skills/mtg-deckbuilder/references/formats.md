# Format Rules

validate_deck.py enforces all of this mechanically; this file is the human
reference. Legality always comes from the cached Scryfall `legalities`
field — never from memory (post-cutoff sets and recent bannings make memory
wrong).

| Format (aliases) | Deck size | Copy limit | Legality key | Sideboard | Notes |
|---|---|---|---|---|---|
| commander (edh) | exactly 100 incl. commander | 1 (singleton) | `commander` | none | color identity ⊆ commander's; commander in decklist, passed via `--commander` |
| standard | 60 minimum | 4 | `standard` | 15 | |
| pioneer | 60 minimum | 4 | `pioneer` | 15 | |
| modern | 60 minimum | 4 | `modern` | 15 | |
| legacy | 60 minimum | 4 | `legacy` | 15 | |
| pauper | 60 minimum | 4 | `pauper` | 15 | commons-only is captured by the legality field |
| limited (league, sealed, draft) | exactly 40 (override with `--deck-size`) | pool-bound only | none | rest of pool | ~17 lands / 23 spells baseline |
| kitchen (casual, kitchen table) | 60 minimum (overridable) | 4 (overridable) | none | none | house rules via flags |

Everywhere:
- Basic lands (incl. snow, Wastes) are unlimited and exempt from ownership,
  copy-limit and restriction checks.
- `restricted` legality = max 1 copy (relevant if a Vintage-style list is
  requested via kitchen + overrides).
- League/sealed pool restrictions (e.g. "only set ECL") are ownership
  checks against the owned printings in that set: `--restrict-set ecl`.

## Typical land counts by deck size

| Deck | Aggro | Midrange | Control |
|---|---|---|---|
| 40 (limited) | 16-17 | 17 | 17-18 |
| 60 | 18-22 | 24-26 | 26-28 |
| 100 (Commander) | 30-33 + ramp | 35-38 | 38-40 |

## Overlap policy for multi-deck builds

- **shared pool** — decks are alternatives; build one at a time; the same
  physical copies may appear in several decks. No ledger.
- **simultaneous** — all decks must be buildable at once. Pass the same
  `--ledger ledger.json` to every validate_deck.py call (in build order);
  each export records the copies it consumed and later decks can't reuse
  them. Delete the ledger file to start a fresh run.
