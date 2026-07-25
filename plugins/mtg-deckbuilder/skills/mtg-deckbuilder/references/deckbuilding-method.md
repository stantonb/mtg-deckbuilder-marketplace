# Deckbuilding Method

Professional deck construction, distilled from the Draftsim build guide and
extended with competitive practice. Follow the steps in order; every step
produces something that belongs in the final report (the decision AND the
reasoning). All counts scale to the actual deck size — the reference numbers
below are for 60 cards; multiply by 2/3 for 40, by 5/3 for 99/100.

## 1. Pick strategy from the pool, not from hope

Score what the collection actually supports BEFORE choosing an archetype.
Count, per color pair: creatures at 1-3 MV, removal/interaction pieces,
card-advantage engines, finishers, and mana fixing. The archetype falls out
of the strongest counts:

| Archetype | Identity | Lands (of 60) | Curve peak |
|---|---|---|---|
| Aggro | creature-dense, low curve, reach | 18-22 | 1-2 MV |
| Midrange | efficient threats + interaction | 24-26 | 2-3 MV |
| Control | answers + card advantage + few wincons | 26-28 | 2-4 MV, big top |
| Combo | tutors/redundancy + protection | 20-26 | around the combo |

If a requested archetype scores badly in the pool, say so and recommend what
the pool actually supports. A mediocre aggro pool forced into aggro loses to
a good midrange pool every time.

## 2. Colors

Fewer colors = faster, more consistent. Add a color only for a real payoff
(a bomb, a whole removal suite), and only if the fixing exists: duals,
treasures, landcyclers, mana creatures. Two colors is the default; mono is
better when the pool allows; three needs 3+ real fixers.

## 3. Quantities

Critical cards at the maximum allowed copies; situational cards 1-3.
In singleton formats redundancy = functional duplicates (count effects, not
names: 8 "Llanowar Elves-alikes" is 8 copies of one card).

## 4. Mana curve

Inverted U peaking at 2-3 MV, shaped by archetype (aggro peaks at 1-2 and
tops out ~4; control tolerates a bigger top end because it trades early).
Compute and report: average MV of nonlands, curve histogram, and the count
of proactive turn-1/turn-2 plays. goldfish.py prints all three.

## 5. Mana base engineering

Count colored pips per color across the deck (goldfish.py reports this),
weight by how early each card must land, and set the land split
proportionally to pips — then nudge toward the color needed EARLIEST.
Karsten-style source minimums for competitive 60-card decks (scale to size):

| Need | Sources (60-card) | 40-card | 99-card |
|---|---|---|---|
| C on turn 1 (e.g. {B} discard) | 14 | 9 | 20 |
| CC by turn 2-3 (e.g. {W}{W}) | 20 | 13 | 28 |
| Splash single pip turn 4+ | 9-12 | 6-8 | 14-18 |

If the deck can't meet the sources for a card's pips, cut the card or fix
the mana — don't ship it and hope. Report the math (pips per color, sources
per color) in the report.

## 6. Interaction minimums

Enough removal/interaction for the format: roughly 6-8 pieces in a 40-card
limited deck, 8-12 in 60-card midrange, more in control shells, ~10+ in
Commander (spot + sweepers). For each answer note what it can and cannot
hit (creatures only? power 3 or less? no regeneration matters? sorcery
speed?). A removal suite that can't touch the format's key threats isn't a
removal suite.

## 7. Card advantage

Identify the engines: raw draw, recursion, impulse/exile-draw, token
value, ETB re-use. A deck with zero engines is either a deliberate
all-in tempo choice (say so in the report) or a bug (fix it).

## 8. Win conditions and reach

Name exactly how the deck wins — which cards, by which turn (the goldfish
sim's wincon metric verifies the turn). Then check the deck can close a
STALLED board: evasion (flying, menace, trample), reach (burn, drain), or
inevitability (a grindy engine). A ground-creature deck with none of these
gets flagged.

## 9. Synergy density — engine over pile

Every card either advances the plan or answers the opponent's; anything
else is a "good card, wrong deck" inclusion — flag it and usually cut it.
When N decks are requested, make them genuinely distinct archetypes with
different play patterns — never near-duplicates (two decks sharing a color
pair must still differ in plan, curve, and core engine).

## 10. Sideboard (formats that use one)

15 cards targeting the expected metagame. Each sideboard card names the
matchup(s) it comes in for and what comes out. Include a short sideboarding
guide per common archetype in the report.

## 11. Iterate after playtesting

The first build is a draft. After the goldfish run and sample games:
- keepable-hand rate < ~80% or screw rate > ~15% → fix lands/curve
- colour screw > ~10% on turns 2-3 → fix the mana base or cut the pips
- curve-out numbers weak for an aggro deck → lower the curve
- wincon deploy turn too late for the plan → add redundancy or cheaper wincons
Change the deck, re-run validate_deck.py and goldfish.py, and record in the
report what changed and why. One or two iterations is normal; zero is
suspicious.

## Narrated sample games

Play 2-3 short games per deck on paper (not a full log — one paragraph per
game with the lesson learned). At least one game must be a hostile
scenario: an aggro rush by turn 4, a board wipe on turn 5, or heavy
removal. These surface qualitative failure modes the goldfish can't see
(e.g. "everything dies to one sweeper", "hand is gas but nothing to do
before turn 3").
