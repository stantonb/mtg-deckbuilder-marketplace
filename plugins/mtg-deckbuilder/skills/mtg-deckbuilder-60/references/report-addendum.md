# Report addendum — 60-card constructed

Follow `../../mtg-deckbuilder/references/report-spec.md` exactly (single
self-contained HTML file in the run folder, all required sections). Add
these sections per deck, in this order, after "Decisions":

## A. Copy-count rationale

A table of every nonland card: name, copies, one-line reason for the count
(4-of core / 3 for diminishing returns / 2 legendary or situational / 1
tutor target). Cards whose count is limited by owned copies say so
("2 owned").

## B. Land math

The land count chosen, the archetype target range it sits in, the
hypergeometric row for that count (P(2-4 lands), P(0-1 lands), expected
lands by turn 4 — from `sixty-card-method.md` §3) and the Karsten source
check: for each colour, pips, earliest turn needed, sources required,
sources in the deck. Enters-tapped land count.

## C. Sideboard guide

(When the format has a sideboard.) The 15 cards, each with the matchup(s)
it targets. Then a per-archetype table — aggro, control, midrange, combo,
go-wide, graveyard — with **In** / **Out** columns and one line of
reasoning. If a matchup gets no changes, say so.

## D. Legality statement

The format, the cache field consulted (`legalities.<format>`), the date
of the cache snapshot (`_meta.updated`), and a note that rotation or bans
after that date would need a re-validate. For kitchen table: "no legality
gate applied; list is legal in <format>/none as of the snapshot."

## Matchups section (report-spec §6)

Keep the six-archetype grid; add a "post-sideboard" rating column when a
sideboard exists.

## Iteration log

Include the `deck_audit.py` counts before and after any change that was
driven by an out-of-range finding.
