# Report addendum — Commander

Follow `../../mtg-deckbuilder/references/report-spec.md` exactly (single
self-contained HTML file in the run folder, all required sections; the
"Sideboard" heading reads "none in Commander"). Header shows the commander
first, its colour identity, bracket target and land/ramp counts. Add these
sections per deck after "Decisions":

## A. Commander choice

The shortlist considered (up to 3), with the pool-scoring evidence per
candidate: owned commander-legal cards in identity, package coverage
(ramp / card advantage / interaction / synergy counts from `deck_audit.py`),
and the one-paragraph reason the winner was chosen. If the user named the
commander, state whether the pool supports it and what was thin.

## B. Package table

Eight rows (ramp, card advantage, interaction, protection/recursion,
enablers, payoffs, synergy glue, win conditions) — target count, actual
count, and the card names in each. Note every card that sits in two
packages. Lands are their own row.

## C. Mana allocation

Per colour: coloured pips (incl. commander), pip %, nonland cards, card %,
land sources, source %, plus the commander-cost weighting applied. Total
mana sources (lands + ramp) and the land-math row for the land count
(`commander-method.md` §5). Enters-tapped land count.

## D. Bracket self-assessment

The bracket requested and the checklist: Game Changers present (from the
list supplied — say "list supplied by user on <date>" or "not checked —
no current list supplied"), 2-card infinite combos (named or "none"), mass
land denial, extra-turn chaining, tutor count, average turn a win is
threatened (goldfish wincon metric), and a one-line verdict on whether the
deck sits in the requested bracket.

## Playtest statistics (report-spec §4)

Add the commander rows: `commander_avg_cast_turn`,
`commander_cast_by_t10_pct`, `ramp_deployed_by_t3_pct`,
`avg_mana_sources_t4`. Bold anything outside `commander-method.md` §8.

## Matchups (report-spec §6) — pod version

Replace the six 1v1 archetypes with six pod opponents: fast aggro /
voltron, stax / control, combo, go-wide tokens, graveyard / reanimator,
big-mana battlecruiser. Same columns (rating, why, key cards), plus a
"threat assessment" paragraph: what in this deck draws the table's
removal first, and what to hold back.

## Sample games (report-spec §5)

Four-player pod narratives as required by the skill: archenemy + sweeper,
vs. fast combo/voltron, and a win. Each ends with the lesson.

## Upgrades (when suggest-upgrades is on)

Group the 5-10 suggestions by package, with the cached price and what
each replaces — the guide's "upgrade pathway".
