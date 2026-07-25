# HTML Report Specification

One single self-contained HTML file per run, covering ALL requested decks.
Save it inside the run's output folder (`$OUT` from SKILL.md — the folder
that also holds the exported decklists) as
`<Run Name> Deck Report <YYYYMMDD-HHMMSS>.html`
(timestamped — re-runs must never overwrite earlier reports).

## Self-contained means self-contained

- All CSS and JS inline. No CDN links, no external images, no web fonts.
  The file must render fully offline.
- Charts as inline SVG or pure-CSS bars (a data-visualization skill, if one
  is available in the session, may generate them — but the output still
  gets inlined). Keep charts legible in both light backgrounds and print.

## Required sections (per deck)

1. **Header** — deck name, format, archetype, colors, deck size, land
   count, average MV, power target. The Moxfield-importable list in a
   `<pre>` block with a copy button.
2. **Decisions** — why this archetype (the pool-scoring evidence), why
   these colors, the mana-base math (pips per color vs. sources per
   color), and **cards that just missed the cut and why** (at least 3-5,
   each one sentence).
3. **Charts** — mana curve histogram, colored-pip breakdown, card-type
   breakdown. Data comes straight from goldfish.py output.
4. **Playtest statistics** — the full goldfish.py numbers, play and draw:
   keepable-hand %, mulligan %, missed-drop by turn, colour screw by turn,
   curve-out by turn, flood/screw rates, wincon deploy turn. Present as a
   table; bold anything outside the method's thresholds and say what was
   done about it (iteration note).
5. **Sample games** — one short paragraph per narrated game (2-3 games,
   at least one hostile scenario) ending with the lesson learned.
6. **Matchups** — strengths and weaknesses vs. the six standard
   archetypes: aggro, control, midrange, combo, go-wide, graveyard.
   One row each: rating (favored/even/unfavored), one-line why, the key
   card(s) in the matchup.
7. **Iteration log** — what changed after playtesting and why (or an
   explicit "first build survived testing unchanged because ...").

## Additional sections when N > 1 decks

- **Ranked comparison** — a table ranking the decks (power, consistency,
  speed, interaction), with one paragraph justifying the order.
- **Card overlap** — if the pool is shared: a matrix of cards appearing in
  more than one deck. If simultaneous: state that overlap is zero by
  construction (ledger-enforced).

## Additional sections when suggest-upgrades is on

Per deck: the best cards NOT in the collection (5-10), each with its
current price from the cache's price snapshot, and one line on what it
replaces/improves. Cards must have been validated through card_cache.py
lookup (never priced from memory).

## Quality bar

Every number in the report must trace to a script output (goldfish.py,
validate_deck.py, card_cache.py) — no invented statistics. Every card name
mentioned must have been cache-validated. If a section is intentionally
empty (e.g. no sideboard in Commander), say so rather than omitting the
heading.
