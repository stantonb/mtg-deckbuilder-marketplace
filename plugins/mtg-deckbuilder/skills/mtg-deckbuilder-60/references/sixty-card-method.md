# 60-Card Constructed Method

Extends the generic method in `../../mtg-deckbuilder/references/deckbuilding-method.md`
(pool scoring, synergy pass, narrated games) with the 60-card specifics,
distilled from the ManaBuilder "60-card deck secrets" guide and competitive
practice (Karsten mana math). Follow the sections in order; each produces a
decision that belongs in the report.

## 1. Exactly 60 — the minimum is the maximum

Sanctioned formats say "at least 60"; play exactly 60. Every card above 60
lowers the odds of drawing your best cards. `validate_deck.py --deck-size 60`
enforces it. If a 61st card "has to" make the deck, something else is
weaker — cut that instead.

Pool scoring first (generic method §1): before choosing an archetype,
count per colour pair the format-legal cards the collection owns **in
multiples** — a 4-of plan needs 4 owned copies. Constructed is defined by
its 4-ofs, so a colour pair with eight strong 4-of-able cards beats one
with twenty singletons.

## 2. The skeleton

Baseline for a creature-based 60 (the ManaBuilder split):

| Slot | Count | Share |
|---|---|---|
| Lands | 24 | 40% |
| Creatures | 24-28 | ~45% |
| Noncreature spells | 8-12 | ~15% |

Shape it by archetype:

| Archetype | Lands | Creatures | Noncreature | Curve peak | Top end (5+) |
|---|---|---|---|---|---|
| Aggro | 20-22 (18-20 only with 12+ one-drops and nothing above 3) | 24-30 | 6-12 burn/pump | 1-2 | 0-2 |
| Midrange | 23-25 | 16-24 | 10-16 | 2-3 | 3-6 |
| Control | 25-27 | 2-10 | 24-30 | 2-4 | 4-8 finishers/sweepers |
| Ramp / big | 25-26 + ramp spells | 12-20 | 12-18 | 2 then 5-6 | 8-12 |
| Combo | 20-23 | varies | varies | around the combo | few |

Land adjustments from the guide: almost all cards at 1-2 MV → go down to
22; many 5+ MV cards → 25-26. Never below 18 or above 28 without a
sentence of justification in the report.

## 3. Land math (60 cards, 7-card hand)

| Lands | P(2-4 lands in 7) | P(2-5 lands) | P(0-1 lands) | Expected lands by turn 4 (play) |
|---|---|---|---|---|
| 22 | 75.4% | 80.2% | 19.0% | 3.67 |
| 23 | 76.7% | 82.5% | 16.5% | 3.83 |
| 24 | 77.5% | 84.4% | 14.3% | 4.00 |
| 25 | 77.8% | 86.0% | 12.2% | 4.17 |
| 26 | 77.8% | 87.4% | 10.4% | 4.33 |

24 lands ≈ 40% land draws — one land per turn on average through turn 4,
which is what a curve topping at 4 needs. Cheap card draw and cantrips
count as roughly half a land each for flood/screw purposes; MDFC lands
count as lands.

## 4. Four-of philosophy

Probability of seeing at least one copy in a 60-card deck:

| Copies | Opening 7 | By turn 4 on the play (10 cards) | By turn 4 on the draw (11) |
|---|---|---|---|
| 4 | 39.9% | 52.8% | 56.6% |
| 3 | 31.5% | 42.7% | 46.2% |
| 2 | 22.1% | 30.8% | 33.6% |
| 1 | 11.7% | 16.7% | 18.3% |

Rules of thumb:
- **4 copies**: anything the strategy depends on — enablers, the best cheap
  removal, one- and two-drops in aggro, the premium card advantage engine.
  "Roughly 40% to have it in the opening hand plus early draws."
- **3 copies**: cards you want early but not in multiples (a second copy is
  dead), or a slightly worse redundant version of a 4-of.
- **2 copies**: legendary permanents, situational answers, expensive
  finishers you want to draw late.
- **1 copy**: tutor targets and silver bullets only — a 1-of you "want to
  see" is a bug.
- Each copy count gets one line of rationale in the report.

Redundancy beats raw power: 4 copies of the second-best two-drop is more
consistent than 2 + 2 of two different ones with different colour pips.

## 5. Mana curve — the bell

Distribution of nonland cards:
- **1-2 MV**: early plays that create momentum — aggro wants 16-24 here,
  midrange 10-14, control 8-12 (mostly interaction).
- **3-4 MV**: the body of the deck (the guide's "majority" for creature
  decks); competitive aggro/midrange peaks one step earlier at 2-3.
- **5+ MV**: only game-winning cards. "If your curve is flat and stacked at
  5+ mana, you will likely lose the game before you cast a single spell."

`goldfish.py` prints the histogram and average MV; `deck_audit.py` flags a
top-heavy average for the archetype. Targets: aggro avg MV ≤ 2.4, midrange
≤ 3.0, control ≤ 3.4 (nonland only).

## 6. Colours and the mana base

Two colours by default, one when the pool allows, three only with 3+ real
fixers (duals, fetch-alikes, treasures). Split lands by **coloured pips**
(goldfish.py reports `colored_pip_counts`), then nudge toward the colour
needed **earliest**. With even pips: 12/12 basics is the guide's default;
dual lands replace basics one-for-one.

Karsten source minimums (60 cards, ~90% castability on curve):

| Requirement | Turn 1 | Turn 2 | Turn 3 | Turn 4 | Turn 5 |
|---|---|---|---|---|---|
| Single pip (C) | 14 | 13 | 12 | 11 | 10 |
| Double pip (CC) | — | 20 | 18 | 16 | 15 |
| Splash pip (turn 4+) | — | — | — | 9-12 | 9-12 |

Report the arithmetic: pips per colour, sources per colour, the earliest
turn each colour is needed. If a card's pips can't be met, cut the card or
fix the mana — don't ship and hope. Enters-tapped lands: at most 4-6 in
aggro, 6-8 elsewhere (goldfish treats "unless" lands as untapped —
optimistic; say so).

## 7. Interaction, card advantage, win conditions

- **Interaction**: aggro 4-8 (burn doubles as reach), midrange 8-12,
  control 12-20 incl. 2-4 sweepers. Each answer gets a note on what it
  can't hit (only creatures? power ≤ 3? sorcery speed?).
- **Card advantage**: midrange 3-8 engines, control 6-12; aggro may run
  zero on purpose (say so).
- **Win conditions**: name them and the turn they close (goldfish wincon
  metric). Check the deck beats a **stalled board**: evasion, reach or
  inevitability. Aggro needs reach (burn, haste, pump); control needs 2-4
  resilient finishers and a plan against decking itself in mirrors.

`deck_audit.py --template sixty --archetype <a>` counts all three against
the archetype's ranges from verified oracle text.

## 8. Sideboard (15, sanctioned formats)

Build the 15 against the expected metagame; default to the six standard
archetypes (aggro, control, midrange, combo, go-wide, graveyard):

| Slot | Typical count | Examples of role |
|---|---|---|
| vs. aggro / go-wide | 4-6 | cheap removal, lifegain, sweepers, blockers |
| vs. control / grindy | 3-5 | discard-proof threats, uncounterable/haste, card advantage |
| vs. combo / graveyard / artifacts | 2-4 | graveyard hate, counters, artifact/enchantment removal |
| flexible | 1-3 | extra copies of a maindeck answer, a curve-topper for the play/draw |

Every sideboard card names the matchup(s) it comes in for **and what comes
out**; the report carries a per-archetype sideboarding table. Cards owned
only in 1-2 copies are natural sideboard candidates. Kitchen table: no
sideboard unless asked.

## 9. Legality

Legality comes from the cache's `legalities` field only — Standard rotates
and bannings change; never recall it. Pauper's commons-only rule is
captured by `legalities.pauper`. For kitchen table, no legality gate, but
state which format the list would be legal in if any.

## 10. Playtest thresholds (60 cards)

After `goldfish.py` (5000 games per side):

| Metric | Aggro | Midrange | Control |
|---|---|---|---|
| Keepable hands | ≥ 85% | ≥ 82% | ≥ 80% |
| Screw (< 3 sources turn 3) | ≤ 12% | ≤ 12% | ≤ 10% |
| Colour screw turns 2-3 | ≤ 8% | ≤ 10% | ≤ 10% |
| On-curve turn 2 | ≥ 75% | ≥ 65% | — |
| Curve-out through turn 3 | ≥ 45% | ≥ 30% | — |
| Flood by turn 10 | ≤ 12% | ≤ 15% | ≤ 18% |
| Wincon first cast (avg) | ≤ turn 3 | ≤ turn 4.5 | ≤ turn 6 |

Outside a threshold → change lands/curve/pips, re-run validate, audit and
goldfish, and log the change. Bold the offending numbers in the report and
state what was done (or why it was accepted).

## 11. Narrated games

Two or three per deck, one paragraph each with the lesson. Required
scenarios: on the draw against a faster deck; against a sweeper on turn 4-5
or heavy spot removal; and, when a sideboard exists, one post-board game
naming the swaps. These catch what the goldfish can't — "all my threats die
to one sweeper", "no play before turn 3 on the draw".
