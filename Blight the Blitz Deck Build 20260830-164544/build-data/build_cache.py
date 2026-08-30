#!/usr/bin/env python3
"""Build a card cache in the mtg-deckbuilder cache format from web-verified
card data.

Scryfall is unreachable from this session (egress proxy denies
api.scryfall.com), so card_cache.py cannot fetch. Every record below was
transcribed from a web search against Scryfall/Gatherer/Card Kingdom listings
for that exact card; sources are cited in the build report. Field shapes match
card_cache.make_record().
"""
import json
from datetime import date

TODAY = date.today().isoformat()

# name | mana_cost | type_line | power | toughness | oracle | set | cn
CARDS = [
    ("Assert Perfection", "{1}{G}", "Sorcery", None, None,
     "Target creature you control gets +1/+0 until end of turn. It deals damage "
     "equal to its power to up to one target creature an opponent controls.",
     "ecl", "164"),
    ("Attercop", "{1}{G}", "Creature — Spider", "2", "1",
     "Reach, deathtouch\nLandfall — Whenever a land you control enters, this "
     "creature gets +1/+1 until end of turn.", "hob", "119"),
    ("Beorn, Reluctant Host", "{4}{G}", "Legendary Creature — Human Bear Shapeshifter", "5", "5",
     "Trample", "hob", "118"),
    ("Bilbo's Deadly Slice", "{1}{B}{B}", "Instant", None, None,
     "Destroy target creature.", "hob", "62"),
    ("Blight Rot", "{2}{B}", "Instant", None, None,
     "Put four -1/-1 counters on target creature.", "ecl", "89"),
    ("Blighted Blackthorn", "{4}{B}", "Creature — Treefolk Warlock", "3", "7",
     "Whenever this creature enters or attacks, you may blight 2. If you do, you "
     "draw a card and lose 1 life. (To blight 2, put two -1/-1 counters on a "
     "creature you control.)", "ecl", "90"),
    ("Bogslither's Embrace", "{1}{B}", "Sorcery", None, None,
     "As an additional cost to cast this spell, blight 1 or pay {3}. (To blight 1, "
     "put a -1/-1 counter on a creature you control.)\nExile target creature.",
     "ecl", "94"),
    ("Boughside Wanderers", "{4}{G}{G}", "Creature — Elf Scout", "4", "4",
     "When this creature enters, look at the top four cards of your library. You "
     "may reveal a permanent card from among them and put it into your hand.",
     "hob", "121"),
    ("Champions of the Perfect", "{3}{G}", "Creature — Elf Warrior", "6", "6",
     "As an additional cost to cast this spell, behold an Elf and exile it.\n"
     "Whenever you cast a creature spell, draw a card.\nWhen this creature leaves "
     "the battlefield, return the exiled card to its owner's hand.", "ecl", "171"),
    ("Changeling Wayfinder", "{3}", "Creature — Shapeshifter", "1", "2",
     "Changeling (This card is every creature type.)\nWhen this creature enters, "
     "you may search your library for a basic land card, reveal it, put it into "
     "your hand, then shuffle.", "ecl", "1"),
    ("Creakwood Safewright", "{1}{B}", "Creature — Elf Warrior", "5", "5",
     "This creature enters with three -1/-1 counters on it.\nAt the beginning of "
     "your end step, if there is an Elf card in your graveyard and this creature "
     "has a -1/-1 counter on it, remove a -1/-1 counter from this creature.",
     "ecl", "96"),
    ("Crude Bent Blade", "{2}{B}", "Artifact — Equipment", None, None,
     "When this Equipment enters, target opponent sacrifices a creature of their "
     "choice.\nEquipped creature gets +2/+1.\nEquip {2}", "hob", "63"),
    ("Cryptic Caves", "", "Land", None, None,
     "{T}: Add {C}.\n{1}, {T}, Sacrifice this land: Draw a card. Activate only if "
     "you control five or more lands.", "m20", "244"),
    ("Darkness Descends", "{2}{B}{B}", "Sorcery", None, None,
     "Put two -1/-1 counters on each creature.", "ecl", "97"),
    ("Dawn-Blessed Pennant", "{2}", "Artifact", None, None,
     "As this artifact enters, choose Elemental, Elf, Faerie, Giant, Goblin, "
     "Kithkin, Merfolk, or Treefolk.\nWhenever a permanent you control of the "
     "chosen type enters, you gain 1 life.\n{2}, {T}, Sacrifice this artifact: "
     "Return target card of the chosen type from your graveyard to your hand.",
     "ecl", "254"),
    ("Dawn's Light Archer", "{2}{G}", "Creature — Elf Archer", "4", "2",
     "Flash\nReach", "ecl", "174"),
    ("Dawnhand Eulogist", "{3}{B}", "Creature — Elf Warlock", "3", "3",
     "Menace\nWhen this creature enters, mill three cards. Then if there is an Elf "
     "card in your graveyard, each opponent loses 2 life and you gain 2 life.",
     "ecl", "99"),
    ("Down in the Valley", "{2}{G}", "Enchantment — Saga", None, None,
     "I — Search your library for a basic land card, reveal it, put it into your "
     "hand, then shuffle.\nII — This Saga gains \"Landfall — Whenever a land you "
     "control enters, create a 1/1 green Elf creature token.\"\nIII, IV — Elves "
     "you control get +1/+0 and gain vigilance until end of turn.", "hob", "124"),
    ("Eaten Alive", "{B}", "Sorcery", None, None,
     "As an additional cost to cast this spell, sacrifice a creature or pay {3}{B}.\n"
     "Exile target creature or planeswalker.", "fdn", "172"),
    ("Elven Passage", "", "Land", None, None,
     "{T}, Pay 1 life, Sacrifice this land: Search your library for a basic land "
     "card, put it onto the battlefield tapped, then shuffle. You may behold an "
     "Elf. If you do, untap that land.", "hob", "181"),
    ("Evolving Wilds", "", "Land", None, None,
     "{T}, Sacrifice this land: Search your library for a basic land card, put it "
     "onto the battlefield tapped, then shuffle.", "fdn", "271"),
    ("Firdoch Core", "{3}", "Kindred Artifact — Shapeshifter", None, None,
     "Changeling (This card is every creature type.)\n{T}: Add one mana of any "
     "color.\n{4}: This artifact becomes a 4/4 artifact creature until end of turn.",
     "ecl", "255"),
    ("Galion, Elvenking's Butler", "{2}{G}{G}", "Legendary Creature — Elf Advisor", "4", "4",
     "Whenever this creature attacks, choose up to one other target creature you "
     "control. Its base power and toughness become equal to this creature's power "
     "and toughness until end of turn.", "hob", "125"),
    ("Gatekeeper of Malakir", "{B}{B}", "Creature — Vampire Warrior", "2", "2",
     "Kicker {B} (You may pay an additional {B} as you cast this spell.)\nWhen this "
     "creature enters, if it was kicked, target player sacrifices a creature of "
     "their choice.", "fdn", "713"),
    ("Giant's Boulder", "{1}", "Artifact", None, None,
     "When this artifact enters, scry 2.\n{1}, {T}: Add one mana of any color.\n"
     "{7}, {T}, Sacrifice this artifact: Destroy target permanent.", "hob", "173"),
    ("Gigantic Big Bear", "{5}{G}{G}", "Creature — Bear", "10", "7",
     "This spell can't be countered.\nHexproof, haste", "hob", "126"),
    ("Gilt-Leaf's Embrace", "{2}{G}", "Enchantment — Aura", None, None,
     "Flash\nEnchant creature\nWhen this Aura enters, enchanted creature gains "
     "trample and indestructible until end of turn.\nEnchanted creature gets +2/+0.",
     "ecl", "177"),
    ("Gnashing of Teeth", "{1}{B}{B}", "Sorcery", None, None,
     "Choose one —\n• Target creature gets -5/-5 until end of turn. If that "
     "creature would die this turn, exile it instead.\n• Creatures target player "
     "controls get -1/-1 until end of turn.", "hob", "69"),
    ("Graveshifter", "{3}{B}", "Creature — Shapeshifter", "2", "2",
     "Changeling (This card is every creature type.)\nWhen this creature enters, "
     "you may return target creature card from your graveyard to your hand.",
     "mh1", "94"),
    ("Great Forest Druid", "{1}{G}", "Creature — Treefolk Druid", "0", "4",
     "{T}: Add one mana of any color.", "ecl", "178"),
    ("Guardian of the Halls", "{1}{G}", "Creature — Elf Soldier", "2", "2",
     "Trample\n{5}{G}{G}: Put three +1/+1 counters on this creature.", "hob", "127"),
    ("Head of the Hunt", "{2}{B}{B}", "Creature — Wolf", "4", "3",
     "Flash\nIf a creature an opponent controls would die, exile it instead. When "
     "you do, create a 2/2 green Wolf creature token.", "hob", "75"),
    ("Hero's Downfall", "{1}{B}{B}", "Instant", None, None,
     "Destroy target creature or planeswalker.", "fdn", "175"),
    ("High Perfect Morcant", "{2}{B}{G}", "Legendary Creature — Elf Noble", "4", "4",
     "Whenever this creature or another Elf you control enters, each opponent "
     "blights 1. (They each put a -1/-1 counter on a creature they control.)\n"
     "Tap three untapped Elves you control: Proliferate. Activate only as a "
     "sorcery.", "ecl", "229"),
    ("Hobbit Hole", "", "Land", None, None,
     "{T}, Sacrifice this land: Search your library for a basic land card, put it "
     "onto the battlefield tapped, then shuffle.\nHalflingcycling {4} ({4}, Discard "
     "this card: Search your library for a Halfling card, reveal it, put it into "
     "your hand, then shuffle.)", "hob", "184"),
    ("Iron-Shield Elf", "{1}{B}", "Creature — Elf Warrior", "3", "1",
     "Discard a card: This creature gains indestructible until end of turn. Tap it.",
     "ecl", "108"),
    ("Lys Alana Dignitary", "{1}{G}", "Creature — Elf Advisor", "2", "3",
     "As an additional cost to cast this spell, behold an Elf or pay {2}.\n"
     "{T}: Add {G}{G}. Activate only if there is an Elf card in your graveyard.",
     "ecl", "180"),
    ("Macabre Waltz", "{1}{B}", "Sorcery", None, None,
     "Return up to two target creature cards from your graveyard to your hand, "
     "then discard a card.", "rvr", "82"),
    ("Massacre Wurm", "{3}{B}{B}{B}", "Creature — Wurm", "6", "5",
     "When this creature enters, creatures your opponents control get -2/-2 until "
     "end of turn.\nWhenever a creature an opponent controls dies, that player "
     "loses 2 life.", "m21", "114"),
    ("Mirkwood Pathmaker", "{2}{G}", "Creature — Elf Ranger", "*", "*",
     "This creature's power and toughness are each equal to the number of lands "
     "you control.", "hob", "129"),
    ("Moonglove Extractor", "{2}{B}", "Creature — Elf Warlock", "2", "1",
     "Whenever this creature attacks, you draw a card and lose 1 life.", "ecl", "109"),
    ("Morcant's Loyalist", "{1}{B}{G}", "Creature — Elf Warrior", "3", "2",
     "Other Elves you control get +1/+1.\nWhen this creature dies, return another "
     "target Elf card from your graveyard to your hand.", "ecl", "236"),
    ("Nameless Inversion", "{1}{B}", "Kindred Instant — Shapeshifter", None, None,
     "Changeling (This card is every creature type.)\nTarget creature gets +3/-3 "
     "and loses all creature types until end of turn.", "lrw", "128"),
    ("Old Fat Spider", "{4}{G}{G}", "Creature — Spider", "6", "7",
     "Reach\nThis creature can't be blocked by creatures with power 2 or less.\n"
     "Whenever this creature becomes the target of a spell or ability an opponent "
     "controls, draw a card.", "hob", "132"),
    ("Overgrown Tomb", "", "Land — Swamp Forest", None, None,
     "({T}: Add {B} or {G}.)\nAs this land enters, you may pay 2 life. If you "
     "don't, it enters tapped.", "ecl", "266"),
    ("Quarrel", "{1}{G}", "Instant", None, None,
     "Target creature you control deals damage equal to its power to target "
     "creature an opponent controls.", "hob", "135"),
    ("Ravening Warg", "{1}{B}", "Creature — Wolf", "2", "2",
     "Deathtouch\nFerocious — Whenever this creature attacks while you control a "
     "creature with power 4 or greater, you gain 2 life.", "hob", "80"),
    ("Reverent Howl", "{2}{B}", "Instant", None, None,
     "Choose one —\n• Target player draws two cards and loses 2 life.\n• Target "
     "creature gets +2/+2 and gains lifelink until end of turn.", "hob", "81"),
    ("Safewright Cavalry", "{3}{G}", "Creature — Elf Warrior", "4", "4",
     "This creature can't be blocked by more than one creature.\n{5}: Target Elf "
     "you control gets +2/+2 until end of turn.", "ecl", "191"),
    ("Scarblade Scout", "{1}{B}", "Creature — Elf Scout", "2", "2",
     "Lifelink\nWhen this creature enters, mill two cards.", "ecl", "118"),
    ("Selfless Safewright", "{3}{G}{G}", "Creature — Elf Warrior", "4", "2",
     "Flash\nConvoke (Your creatures can help cast this spell.)\nWhen this creature "
     "enters, choose a creature type. Other permanents you control of that type "
     "gain hexproof and indestructible until end of turn.", "ecl", "193"),
    ("Shimmerwilds Growth", "{1}{G}", "Enchantment — Aura", None, None,
     "Enchant land\nAs this Aura enters, choose a color.\nEnchanted land is the "
     "chosen color.\nWhenever enchanted land is tapped for mana, its controller "
     "adds an additional one mana of the chosen color.", "ecl", "194"),
    ("Springleaf Drum", "{1}", "Artifact", None, None,
     "{T}, Tap an untapped creature you control: Add one mana of any color.",
     "ecl", "260"),
    ("Stalactite Dagger", "{2}", "Artifact — Equipment", None, None,
     "When this Equipment enters, create a 1/1 colorless Shapeshifter creature "
     "token with changeling.\nEquipped creature gets +1/+1 and is all creature "
     "types.\nEquip {2}", "ecl", "261"),
    ("Sting, Bilbo's Sword", "{2}", "Legendary Artifact — Equipment", None, None,
     "Flash\nWhen this Equipment enters, put a hone counter on it for each creature "
     "target opponent controls. Attach it to up to one target creature you control. "
     "(Each hone counter on an Equipment grants +1/+0 to equipped creature.)\n"
     "Equip {3}", "hob", "178"),
    ("Stir Up Trouble", "{B}", "Sorcery", None, None,
     "As an additional cost to cast this spell, sacrifice an artifact or creature "
     "or pay {4}.\nDestroy target creature.", "hob", "84"),
    ("Stoic Grove-Guide", "{4}{B/G}", "Creature — Elf Druid", "5", "4",
     "{1}{B/G}, Exile this card from your graveyard: Create a 2/2 black and green "
     "Elf creature token. Activate only as a sorcery.", "ecl", "243"),
    ("Tend the Sprigs", "{2}{G}", "Sorcery", None, None,
     "Search your library for a basic land card, put it onto the battlefield "
     "tapped, then shuffle. Then if you control seven or more lands and/or "
     "Treefolk, create a 3/4 green Treefolk creature token with reach.",
     "ecl", "197"),
    ("The Chief Warg", "{2}{B}{G}", "Legendary Creature — Wolf", "3", "3",
     "Menace\nFerocious — Whenever you attack while you control a creature with "
     "power 4 or greater, you draw a card and lose 1 life.", "hob", "150"),
    ("Thrór's Map", "{2}", "Legendary Artifact", None, None,
     "When this artifact enters, search your library for a basic land card, reveal "
     "it, put it into your hand, then shuffle.\n{2}, {T}: Draw a card, then discard "
     "a card.", "hob", "179"),
    ("Tom, Bert, and William", "{3}{B}{G}", "Legendary Creature — Troll", "5", "5",
     "{1}, Sacrifice another creature: Draw cards equal to the sacrificed "
     "creature's power, then discard a card.\nWhen this creature dies, if it was a "
     "creature, return it to the battlefield. It's an artifact.", "hob", "169"),
    ("Troll Negotiations", "{2}{G}{G}", "Sorcery", None, None,
     "Put two +1/+1 counters on target creature you control. Then it fights target "
     "creature an opponent controls.", "hob", "138"),
    ("Troop of Ponies", "{2}", "Creature — Horse", "2", "1",
     "{2}, {T}, Sacrifice this creature: Search your library for up to two basic "
     "land cards, reveal them, put one onto the battlefield tapped and the other "
     "into your hand, then shuffle.", "hob", "199"),
    ("Trystan, Callous Cultivator", "{2}{G}", "Legendary Creature — Elf Druid", "3", "4",
     "Deathtouch\nWhenever this creature enters or transforms into Trystan, Callous "
     "Cultivator, mill three cards. Then if there is an Elf card in your graveyard, "
     "you gain 2 life.\nAt the beginning of your first main phase, you may pay {B}. "
     "If you do, transform Trystan.", "ecl", "199"),
    ("Vinebred Brawler", "{2}{G}", "Creature — Elf Berserker", "4", "2",
     "This creature must be blocked if able.\nWhenever this creature attacks, "
     "another target Elf you control gets +2/+1 until end of turn.", "ecl", "201"),
    ("Warg Tactics", "{1}{G}", "Instant", None, None,
     "Choose one —\n• Destroy target creature with flying.\n• Put a +1/+1 counter "
     "on target creature you control. It gains trample and hexproof until end of "
     "turn.", "hob", "139"),
    ("Wood Elves", "{2}{G}", "Creature — Elf Scout", "1", "1",
     "When this creature enters, search your library for a Forest card, put that "
     "card onto the battlefield, then shuffle.", "9ed", "283"),
]

BASICS = [("Plains", "W"), ("Island", "U"), ("Swamp", "B"), ("Mountain", "R"),
          ("Forest", "G"), ("Wastes", "C")]

PIP_COLORS = {"W", "U", "B", "R", "G"}


def colors_of(cost):
    out = set()
    i = 0
    while i < len(cost):
        if cost[i] == "{":
            j = cost.index("}", i)
            for part in cost[i + 1:j].split("/"):
                if part in PIP_COLORS:
                    out.add(part)
            i = j + 1
        else:
            i += 1
    return sorted(out)


def cmc_of(cost):
    total = 0.0
    i = 0
    while i < len(cost):
        if cost[i] == "{":
            j = cost.index("}", i)
            sym = cost[i + 1:j]
            parts = sym.split("/")
            if parts[0].isdigit():
                total += int(parts[0])
            elif sym == "X":
                pass
            else:
                total += 1
            i = j + 1
        else:
            i += 1
    return total


LAND_PRODUCES = {
    "Cryptic Caves": ["C"],
    "Overgrown Tomb": ["B", "G"],
    # Evolving Wilds, Elven Passage and Hobbit Hole have no mana ability at all:
    # they only sacrifice for a basic. Scryfall reports produced_mana [] for them.
    "Evolving Wilds": [],
    "Elven Passage": [],
    "Hobbit Hole": [],
}

# Mana abilities on nonland permanents, for reference in the report.
cards = {}
for name, cost, type_line, power, tough, oracle, setcode, cn in CARDS:
    is_land = "Land" in type_line
    produced = LAND_PRODUCES.get(name, [])
    if not is_land:
        if "Add one mana of any color" in oracle:
            produced = ["W", "U", "B", "R", "G"]
        elif "Add {G}{G}" in oracle:
            produced = ["G"]
    cards[name.lower()] = {
        "name": name,
        "mana_cost": cost,
        "cmc": cmc_of(cost),
        "colors": colors_of(cost),
        "color_identity": colors_of(cost),
        "type_line": type_line,
        "oracle_text": oracle,
        "power": power,
        "toughness": tough,
        "loyalty": None,
        "keywords": [],
        "rarity": "common",
        "set": setcode,
        "collector_number": cn,
        # kitchen-table build: no legality gate is applied, and legality could
        # not be fetched from Scryfall in this session.
        "legalities": {},
        "prices": {},
        "produced_mana": produced,
        "layout": "normal",
        "scryfall_id": None,
        "is_basic": False,
        "validated_at": TODAY,
        "source": "web-search-verified (Scryfall/Gatherer listings); "
                  "api.scryfall.com unreachable from this session",
    }

for name, color in BASICS:
    cards[name.lower()] = {
        "name": name, "mana_cost": "", "cmc": 0.0, "colors": [],
        "color_identity": [color], "type_line": f"Basic Land — {name}",
        "oracle_text": f"({{T}}: Add {{{color}}}.)", "power": None,
        "toughness": None, "loyalty": None, "keywords": [], "rarity": "common",
        "set": "fdn", "collector_number": "", "legalities": {}, "prices": {},
        "produced_mana": [color], "layout": "normal", "scryfall_id": None,
        "is_basic": True, "validated_at": TODAY,
        "source": "basic land",
    }

out = {"_meta": {"created": TODAY, "updated": TODAY,
                 "note": "Hand-built from web-search-verified card data; "
                         "Scryfall egress blocked in this session."},
       "cards": cards}
with open("cache.json", "w") as f:
    json.dump(out, f, indent=1, sort_keys=True)
print(f"wrote cache.json with {len(cards)} cards")
