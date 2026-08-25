# Commander Method — packages, not piles

Distilled from the Three For One Trading Commander deck-build guide and
multiplayer practice, on top of the generic method in
`../../mtg-deckbuilder/references/deckbuilding-method.md`. Commander is a
100-card singleton, 40-life, usually 4-player format: consistency comes
from **functional redundancy**, not copies, and the deck must survive three
opponents, not one.

## 1. Concept, then commander

Write the rough vision first: theme, target bracket, what the playgroup
enjoys or hates. Two valid routes:
- **Top-down**: concept first ("spellslinger graveyard"), then find the
  commander that supports it.
- **Bottom-up**: a card you love first, then the commander that makes it
  shine.

Here the pool is the collection: the commander must be **owned**. Score
each owned legendary candidate by how many owned, commander-legal cards in
its colour identity fill the packages below, and by how directly its text
drives the plan. A commander that "directly supports the plan" beats a
higher-raw-power one the pool can't feed.

## 2. The 100-card skeleton

| Slot | Count |
|---|---|
| Commander | 1 |
| Lands | 35-38 (35 with 10+ ramp and avg MV ≤ 3; 38-40 for high curves / landfall) |
| Nonland | 61-64, organised as eight ~8-card packages |

The guide's formula: **64 + 1 + 35 = 100**. Think in packages so tuning
means "swap one package for another", not agonising over single cards.

## 3. The four utility packages (every deck)

| Package | Target | What counts | Notes from the guide |
|---|---|---|---|
| Ramp | 8-12 | Mana rocks (Signets over Talismans for fixing), mana creatures, land-fetch spells, cost reducers | "Nothing cute, smart, or clever. Just some mana rocks and ways to reduce the cost of our spells." Prefer 2-MV rocks; a 3-MV rock is a payoff-turn tax |
| Card advantage | 8-12 | Raw draw, wheels, impulse ("exile the top… you may play"), selective discard/looting, recursion, graveyard access | Definition is flexible — anything that gives "access to more cards" |
| Interaction | 8-10 spot + 2-4 sweepers | Modal spells, X-cost removal, exile effects, counterspells (weaker if the deck can't react on other turns), fights/edicts | Must answer the format's threats: commanders, enchantments, artifacts, combo pieces — not just creatures |
| Protection / recursion | 3-6 | Hexproof/indestructible grants, counter-that-targets, regrowth, reanimation of the commander's engine | Optional package; grows for voltron and combo, shrinks for go-wide |

`deck_audit.py --template commander` counts these from verified oracle
text (lands 35-40, ramp 8-12, card advantage 8-12, spot removal 6-10,
sweepers 2-4, interaction ≥ 10).

## 4. The four theme packages (defined by the commander)

| Package | ~Count | Role |
|---|---|---|
| Enablers | 8 | Cards that turn the commander on: untappers, cost reducers, trigger sources, token makers, sacrifice outlets — whatever the plan's verb is |
| Payoffs | 8 | Cards that get better as the plan runs (the guide's "creature payoffs" — magecraft, landfall, aristocrats triggers) |
| Synergy glue | 8 | Cheap cards that do two jobs in this deck — copying/doubling, cantrips that fuel the graveyard, ETB re-use — "synergy is what can make a deck shine" |
| Win conditions | 6-8 | How the table actually dies: damage doublers, drain, mill, infinite loops (if the bracket allows), 21 commander damage, overrun effects. Name them; the goldfish wincon metric tracks the deploy turn |

Packages may grow, shrink, merge or be retired after testing. In singleton,
"8 copies" of an effect means 8 different cards that do the same thing.

Probability of seeing at least one of N functional duplicates (99-card library):

| Functional copies | Opening 7 | By turn 4 (10 cards) |
|---|---|---|
| 4 | 25.8% | 35.1% |
| 6 | 36.4% | 48.1% |
| 8 | 45.6% | 58.7% |
| 10 | 53.7% | 67.4% |

That is why the utility packages are 8-12 deep: 8 ramp pieces gives
roughly a coin flip at one by turn 2-3.

## 5. Mana base by pip share

1. Count coloured pips on all nonland cards **and** on the commander
   (goldfish.py `colored_pip_counts` includes the commander).
2. Count nonland cards per colour.
3. Give each colour a share of land sources **between its pip percentage
   and its nonland-card percentage** (within 5-10% of the pip share).
4. Weight the commander's own cost extra — it is cast every game, often
   more than once. If its cost is colour-intensive ({U}{U}{R} say), add 1-2
   sources of that colour above the formula.
5. Multicolour lands first (duals, tri-lands, "slow fetches" such as Bad
   River count toward every colour they fetch), then basics to fill.

Guide example (Kess, Dissident Mage): blue 38 pips / 41%, 28 nonland cards
/ 45% → land sources ~41-45% blue; black 15 / 16%, 10 / 16% → ~16%; red 40 /
43%, 31 / 50% → ~43-50%.

Land math (99-card library, 7-card hand):

| Lands | P(2-5 lands in 7) | P(0-1 lands) | P(3+ lands by turn 3, play) |
|---|---|---|---|
| 35 | 77.5% | 21.8% | 68.1% |
| 36 | 79.0% | 20.1% | 70.4% |
| 37 | 80.4% | 18.6% | 72.7% |
| 38 | 81.7% | 17.1% | 74.8% |
| 40 | 84.0% | 14.4% | 78.8% |

Ramp closes the gap: 36 lands + 10 ramp ≈ 46 mana sources, the usual
target for a deck that wants 4-5 mana on turn 4. Fewer than 44 total
sources needs a low-curve justification. "Nothing feels worse than having
a powerful card rot away in your hand" — land count is not where to be
greedy.

## 6. Curve and multiplayer realities

- Average nonland MV ≤ 3.6 for most decks (battlecruiser tables tolerate
  more; say so). Plenty of 2-MV plays (ramp, cantrips, cheap removal) so
  turns 1-3 are never blank.
- **Three opponents**: one-for-one removal loses value; prefer modal,
  exile, and sweepers that spare your board. Aim removal at the threat
  that ends the game, not the biggest creature.
- **40 life**: aggro must be evasive, doubled or commander-damage based;
  incremental drain and go-wide overruns are the honest routes.
- **Politics**: threats that don't paint a target (value engines) survive
  longer than obvious bombs; keep 1-2 answers in hand when ahead.
- Every card either advances the plan or answers the table; "good card,
  wrong deck" gets flagged and usually cut (generic method §9).

## 7. Brackets (power level)

The Commander Brackets scale, 1-5. The bracket is a **table agreement**,
not a rules gate, but bracket ≤ 2 requests translate into build
restrictions:

| Bracket | Name | Expectations |
|---|---|---|
| 1 | Exhibition | Ultra-casual, theme first; no Game Changers, no infinite combos, no mass land denial, no extra-turn chaining, few tutors |
| 2 | Core | Precon-level; same restrictions as 1, games end by turn ~9+ via board |
| 3 | Upgraded | Tuned; up to 3 Game Changers, late-game 2-card combos acceptable, no mass land denial or extra-turn chaining |
| 4 | Optimized | No restrictions except the ban list; not tuned for cEDH |
| 5 | cEDH | Tournament metagame |

The Game Changers list is maintained by the format's stewards and changes —
take it from the user or fetch it live (Scryfall search `is:gamechanger`,
see SKILL.md Step 0), apply it with `--ban`, and never list Game Changers
from memory. When the user names a bracket, the report
carries a self-assessment: Game Changers present (from the supplied list),
2-card combos (name them or state none), land denial, extra turns, tutor
density, average turn to threaten a win (goldfish wincon metric).

## 8. Playtest thresholds (99-card library, `--commander` mode)

| Metric | Target |
|---|---|
| Keepable hands | ≥ 80% |
| Screw (< 3 sources on turn 3) | ≤ 12% |
| Colour screw turns 2-3 | ≤ 8% (2-colour) / ≤ 12% (3+) |
| Ramp deployed by turn 3 | ≥ 50% (≥ 60% for ramp-heavy plans) |
| Average mana sources on turn 4 | ≥ 4.5 |
| Commander average cast turn | ≤ its MV + 0.5 (≤ MV for a 4-MV-or-less commander the plan depends on) |
| Flood by turn 10 | ≤ 15% |
| Wincon first cast (avg) | consistent with the bracket: bracket 2 ≥ turn 7, bracket 3 ~5-7, bracket 4 ≤ 5 |

Outside a threshold → adjust the offending package (usually lands/ramp
count or the curve), re-run validate, audit and goldfish, log the change.
"Deck building is a journey. It is rarely 'finished'."

## 9. Narrated pod games

Two or three per deck, one paragraph each with the lesson, in a
four-player pod: (a) the deck becomes archenemy and eats a sweeper — does
it rebuild? (b) a fast combo or voltron opponent — does it hold the right
interaction at the right time? (c) a normal game to the win — which package
closed it and on what turn? Use only cache-verified card behaviour.
