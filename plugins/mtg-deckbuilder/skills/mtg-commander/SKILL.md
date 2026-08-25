---
name: mtg-commander
description: "Use whenever the user wants a Commander / EDH deck (100-card singleton, 99 + commander) built, rebuilt, upgraded, bracket-assessed, evaluated or playtested from cards they own, or wants help choosing a commander from their collection. Trigger on 'build me a Commander deck from my collection', 'which commander should I run from my cards', 'make an EDH deck around X', 'is this list bracket 2', 'check my Commander list against my collection', 'goldfish my EDH deck', and any mention of EDH, commander, color identity, brackets, Game Changers or a 100-card deck alongside a collection file. Not for 40-card limited (mtg-deckbuilder) or 60-card constructed (mtg-deckbuilder-60)."
---

# MTG Commander Deckbuilder

Builds Commander (EDH) decks **using only cards the user owns**, with the
package method in `references/commander-method.md` (1 commander + 35-38
lands + eight ~8-card packages), validates colour identity and singleton
rules, playtests with a command-zone-aware goldfish simulator, and
delivers a Moxfield-ready decklist plus a self-contained HTML report.

This skill shares its toolkit with the sibling `mtg-deckbuilder` skill:
scripts, card cache, and the generic method / format / report references
live there. Set once at the start:

```bash
SKILL="<this skill's base directory — shown when the skill loads>"
CORE="$SKILL/../mtg-deckbuilder"          # shared scripts + cache + references
WORK=$(mktemp -d)                          # intermediates only — never shown to the user
OUT="<project dir>/<Run Name> Deck Build $(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"                            # ALL final deliverables go here
```

Scripts: `python3 $CORE/scripts/<name>.py` (stdlib only). Cache:
`$CORE/MTG_Card_Cache.json` unless `MTG_CARD_CACHE` relocates it.

## Two iron rules (same as the core skill)

1. **Card truth comes from the cache, never from memory.** Oracle text,
   colour identity, `commander` legality and prices all come from the
   cache; misses are fetched by `card_cache.py`. This matters doubly in
   Commander: bannings, the Game Changers list and new commanders change
   often. A failed lookup is shown to the user with the printed fuzzy
   suggestions — never guessed, never dropped.
2. **Every deck passes `validate_deck.py --format commander --commander
   "<Name>"` before the user sees it** — exactly 100 cards, singleton,
   colour identity inside the commander's, every card owned.

## Step 0 — Gather inputs

Ask for whatever is missing (defaults in parentheses):

1. Collection CSV path (required)
2. Commander (or "help me choose" — Step 2 then shortlists owned
   candidates). A legendary creature the user owns, or any owned card whose
   oracle text says it can be your commander (partners/backgrounds count
   as two cards).
3. Theme / plan (from the commander's text if not given)
4. Bracket target 1-5 (3 "Upgraded" — see method §7) and playgroup notes
   (none). A bracket ≤ 2 request is also a restriction: no Game Changers,
   no 2-card infinite combos, no mass land denial, no extra-turn chaining.
   Get the current Game Changers list from the user or live from Scryfall —
   never from memory, it changes:

   ```bash
   curl -s -A "mtg-deckbuilder-skill" \
     "https://api.scryfall.com/cards/search?q=is%3Agamechanger&order=name" \
     | python3 -c 'import json,sys; d=json.load(sys.stdin); print(";".join(c["name"] for c in d["data"]))'
   ```

   (Follow `next_page` if `has_more` is true.) Pass the result to
   `validate_deck.py --ban` and cite the fetch date in the report.
5. Restrictions, freeform (none): ban list, must-includes, "no infinite
   combos", "no stax", budget of owned copies
6. Number of decks (1) and, when N > 1, overlap policy (**must ask**):
   `shared pool` or `simultaneous`
7. `suggest-upgrades` flag (off)

## Step 1 — Parse and validate the collection

```bash
python3 $CORE/scripts/parse_collection.py "<collection.csv>" --out $WORK/collection.json
python3 $CORE/scripts/card_cache.py validate --collection $WORK/collection.json --out $WORK/enriched.json
```

`validate` exits 2 if any card failed — report those with the suggestions
first. Read `$WORK/enriched.json` selectively with python: filter to
`legalities.commander == "legal"` and, once a commander is chosen, to
`color_identity ⊆ commander's`.

## Step 2 — Choose the commander from the pool

Concept first or card first (method §1) — but the commander **must be
owned**. With python over `enriched.json`:

1. List owned legendary creatures (type line contains "Legendary" and
   "Creature") plus cards whose oracle text contains "can be your
   commander".
2. For each candidate, count the owned, commander-legal cards inside its
   colour identity by package: ramp, card advantage, spot removal,
   sweepers, and cards that synergise with the commander's text
   (`deck_audit.py` roles help — run it on a throwaway list of the whole
   in-identity pool with `--template commander` to get the counts).
3. Shortlist the top 3 with one paragraph each: plan, package coverage,
   what the pool lacks. If the user named a commander, still run the
   check and say plainly if the pool can't support it (and what it can).

Pick (or let the user pick) and record the reasoning — the report has a
"Commander choice" section.

## Step 3 — Design with packages

Follow `references/commander-method.md`: 1 commander + 35-38 lands +
~61-64 nonland cards in eight ~8-card packages — the four **utility**
packages every deck needs (ramp, card advantage, interaction, protection /
recursion) and four **theme** packages defined by the commander
(enablers, payoffs, synergy glue, win conditions). Singleton means
redundancy = functional duplicates: count effects, not names. Then the
mana base by pip share (method §5). Record decisions, near-miss cuts and
which package each card belongs to.

Write the list as `N Card Name` lines (all `1` except basics), the
commander included as a normal line. Save as `$WORK/deck1.txt`.

## Step 4 — Quality gates (both required)

```bash
python3 $CORE/scripts/validate_deck.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --format commander --commander "<Name>" \
  # plus --ban "A;B" (Game Changers for bracket ≤ 2, house bans) / --require
python3 $CORE/scripts/deck_audit.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --template commander --commander "<Name>"
```

`validate_deck.py` is the gate (exit 1 on any FAIL — fix and re-run).
`deck_audit.py` is advisory: it counts lands / ramp / card advantage /
spot removal / sweepers / creatures against the Commander template and
prints each card's detected roles — override a misread, but justify any
range you leave in the report. Simultaneous policy: `--ledger` on every
validate call, export in build order.

## Step 5 — Playtest (both parts required)

```bash
python3 $CORE/scripts/goldfish.py --deck $WORK/deck1.txt \
  --enriched $WORK/enriched.json --commander "<Name>" \
  --wincons "Card A;Card B" --games 5000 --out $WORK/deck1-goldfish.json
```

`--commander` moves one copy to the command zone (library = 99) and
reports `commander_avg_cast_turn`; mana rocks/dorks and land-fetch spells
are modelled as sources from the following turn (`ramp_deployed_by_t3_pct`,
`avg_mana_sources_t4`).

Then narrate 2-3 short **four-player pod** games (one paragraph + lesson
each): one where the deck is the archenemy and eats a sweeper, one against
a fast combo or voltron player where it must hold interaction, one normal
game to the win. Use only cache-verified card behaviour; note the politics
(who to attack, when to hold removal).

## Step 6 — Iterate

Compare against the thresholds in `references/commander-method.md` §8.
Adjust packages (swap a package, not a card, when a whole plan
under-performs), re-validate, re-audit, re-simulate, log the change.

## Step 7 — Deliver

1. **Decklist**: re-run `validate_deck.py` with `--export-dir "$OUT"
   --deck-name "<Deck Name>"` (+ ledger if simultaneous) for the
   timestamped Moxfield-importable `.txt`. Show it in chat too; put the
   commander on the first line.
2. **HTML report**: one self-contained file in `$OUT` following
   `$CORE/references/report-spec.md` **plus** the Commander sections in
   `references/report-addendum.md` (commander choice, package table, mana
   allocation, bracket self-assessment, pod matchups). Every number traces
   to a script output.
3. If suggest-upgrades was requested: validate candidates through
   `card_cache.py lookup` and use the cached price snapshot; group them by
   package.

## Final checklist before showing output

- [ ] validate_deck.py PASS: 100 cards, singleton, colour identity, commander present, all owned
- [ ] deck_audit.py run with `--commander`; every out-of-range package fixed or justified
- [ ] Every card cache-verified and `commander: legal` per the cache
- [ ] Bracket restrictions honoured (ban list applied for bracket ≤ 2 from a current source)
- [ ] goldfish.py ran with `--commander`; commander cast turn, ramp and screw numbers in the report
- [ ] Pod games narrated (archenemy + sweeper, vs. fast combo/voltron, one win)
- [ ] Mana allocation table (pips %, nonland-card %, land %) in the report
- [ ] Decklist .txt exported (timestamped) + shown in chat, commander first
- [ ] Report is one file, opens offline, all sections present
- [ ] Everything inside `$OUT`; user told the path

## Troubleshooting

| Symptom | Fix |
|---|---|
| `commander format requires --commander` | Pass `--commander "<exact name>"`; the commander must also be a line in the list |
| `X: color identity [...] outside commander's` | Colour identity includes hybrid/activation pips — the cache is right; cut the card |
| `X: 2 copies > limit 1` | Singleton — only basics repeat |
| Partner / Background pair | List both; pass the primary via `--commander`; the second is checked as a normal card (identity union is on you — state it in the report) |
| `deck size 99 != required 100` | The commander counts toward 100 |
| goldfish: `commander ... is not in the decklist` | Same fix — the commander is one of the 100 lines |
| deck_audit misreads a role | Heuristics; override with the oracle text quoted in the report |
| Deck uses a card twice across decks (simultaneous) | Expected — the ledger blocks it; substitute |
