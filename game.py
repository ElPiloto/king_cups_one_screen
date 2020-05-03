"""
TODO(_elpiloto):
  - Add/remove players, insuring:
    - no duplicates
    - don't remove when empty players
  - Add "sub-iteration" for mini-games like categories?

View:
  - new game(rules, players, [num_rounds]) --> take first turn screen (custom version of playing screen)
  - playing screen: 
    + take turn --> playing screen, make new rule
    + add/remove player
"""
from dataclasses import dataclass
from pprint import pprint
import random


VALUE_TO_STRING = {
    1: 'A',
    2: '2',
    3: '3',
    4: '4',
    5: '5',
    6: '6',
    7: '7',
    8: '8',
    9: '9',
    10: '10',
    11: 'J',
    12: 'Q',
    13: 'K',
    14: 'A',
}

SUIT_TO_STRING = {
    0: 'Hearts',
    1: 'Clubs',
    2: 'Diamonds',
    3: 'Spades',
}

@dataclass
class Card:
  value: int
  suit: int

  def __str__(self):
    return '{} of {}'.format(
        VALUE_TO_STRING[self.value],
        SUIT_TO_STRING[self.suit],
        )

  def to_compact_str(self):
    return "{:02d}{}".format(self.value, self.suit)

  @staticmethod
  def from_compact_str(s):
    return Card(value=int(s[:2]), suit=int(s[-1:]))

  def get_image_filename(self):
    value_str = VALUE_TO_STRING[self.value]
    suit_abbrev = SUIT_TO_STRING[self.suit][0]
    return "{}{}.svg".format(value_str, suit_abbrev)


@dataclass
class KingsCupRule:
  # Numeric value of cards where this applies
  value: int
  # Name of rule
  name: str
  # Description of rule
  text: str
  # Makes new rule
  make_custom_rule: bool

  @staticmethod
  def get_rule(rules, card):
    return rules[card.value]

  @staticmethod
  def load_ruleset(filename, expected_num_rules=13):
    """Expects files in following format. Not robust to bad formats.
      value
      name
      text
      bool_make_custom_rule
      ______BLANK_LINE_______
      value
      name
      etc.
    """
    rules = {}
    with open(filename, 'r') as f:
      line_num = 0
      line = f.readline()
      value, name, text, make_custom_rule = -1, "", "", False
      while line:
        if line_num % 5 == 0:
          value = int(line)
        elif line_num % 5 == 1:
          name = line
        elif line_num % 5 == 2:
          text = line
        elif line_num % 5 == 3:
          make_custom_rule = line.lower() == 'true'
        elif line_num % 5 == 4:
          rule = KingsCupRule(value, name, text, make_custom_rule)
          rules[value] = rule
          value, name, text, make_custom_rule = -1, "", "", False

        line_num += 1
        line = f.readline()
    if len(rules) != expected_num_rules:
      raise RuntimeError('Expected {} rules, but only got {} rules.'.format(expected_num_rules, len(rules)))
    return rules

class Deck:

  def __init__(self, aces_high=True, cycle=False, make_deck=True):
    self._aces_high = aces_high
    if make_deck:
      self._deck = self.make_deck(aces_high, shuffled=True)
    else:
      self._deck = []
    self._cycle = cycle

  @staticmethod
  def make_deck(aces_high, shuffled):
    min_v = 2
    max_v = 14
    if not aces_high:
      min_v -= 1
      max_v -= 1
    deck = []
    for s in range(4):
      for v in range(min_v, max_v+1):
        deck.append(Card(value=v, suit=s))
    if shuffled:
      random.shuffle(deck)
    return deck

  def shuffle(self):
    random.shuffle(self._deck)

  def draw(self):
    # TODO(_elpiloto): Add indicator for starting new deck.
    card = self._deck.pop()
    if len(self._deck) == 0:
      if self._cycle:
        self._deck = self.make_deck(self._aces_high, shuffled=True)
      else:
        return None, 0
    num_cards = len(self._deck)
    return card, num_cards

  def __len__(self):
    return len(self._deck)

  def serialize_cards(self):
    return ",".join([c.to_compact_str() for c in self._deck])

  @staticmethod
  def unserialize_cards(compact_str, aces_high, cycle):
    cards = compact_str.split(',')
    d = Deck(aces_high, cycle, make_deck=False)
    for c in cards:
      d._deck.append(Card.from_compact_str(c))
    return d

class KingsCup:

  def __init__(self, players=None, make_deck=True):
    self._deck = Deck(aces_high=True, cycle=True, make_deck=make_deck)
    self._current_player = 0
    if players is None:
      self._players = []
    else:
      self._players = KingsCup.sanitize_players(players)
    self._rules = KingsCupRule.load_ruleset('./rules/covid_rules.txt')
    self._custom_rules = []
    self._total_turns = 0
    self._last_card = ''
    self._current_card = ''
    self._player_who_drew_card = ''

  @staticmethod
  def sanitize_players(players):
    return [p.replace(',', '_comma_').strip() for p in players]

  @staticmethod
  def serialize_custom_rules(custom_rules):
    custom_rule_str = ''
    for p, cr in custom_rules:
      custom_rule_str += '{}|{}`'.format(p, cr)
    return custom_rule_str

  @staticmethod
  def unserialize_custom_rules(custom_rules_str):
    custom_rules = []
    crs = custom_rules_str.split('`')
    for p_cr in crs:
      if p_cr:
        s = p_cr.strip().split('|')
        custom_rules.append((s[0], s[1]))

    return custom_rules

  def serialize(self):
    state = {}
    state['players'] = ','.join(self._players)
    state['deck'] = self._deck.serialize_cards()
    state['custom_rules'] = KingsCup.serialize_custom_rules(self._custom_rules)
    state['current_player'] = self._current_player
    state['total_turns'] = self._total_turns
    state['last_card'] = self._last_card
    state['current_card'] = self._current_card
    state['player_who_drew_card'] = self._player_who_drew_card
    pprint(state)
    return state

  def add_player(self, p):
    self._players.append(p)

  def remove_player(self, p):
    self._players.remove(p)
    if self._current_player >= len(self._players):
      self._current_player = 0

  @staticmethod
  def get_dict_from_session(session):
    state = {}
    state['players'] = session.get('players', '')
    state['deck'] = session.get('deck', '')
    state['custom_rules'] = session.get('custom_rules', '')
    state['current_player'] = session.get('current_player', '')
    state['total_turns'] = session.get('total_turns', '')
    state['last_card'] = session.get('last_card', '')
    state['current_card'] = session.get('current_card', '')
    state['player_who_drew_card'] = session.get('player_who_drew_card', '')
    return state

  @staticmethod
  def unserialize(state):
    players = state['players'].split(',')
    kc = KingsCup(players, make_deck=False)
    deck = Deck.unserialize_cards(state['deck'], aces_high=True, cycle=True)
    kc._deck = deck
    kc._current_player = int(state['current_player'])
    kc._total_turns = int(state['total_turns'])
    kc._last_card = state['last_card']
    kc._current_card = state['current_card']
    kc._player_who_drew_card = state['player_who_drew_card']
    kc._custom_rules = KingsCup.unserialize_custom_rules(state['custom_rules'])
    return kc

  def take_turn(self, should_print=True):
    """Returns player index, player name, card, rule.name, rule.text, rule.make_custom_rule"""
    card, num_cards = self._deck.draw()
    self._last_card = self._current_card
    self._current_card = str(card)
    rule = KingsCupRule.get_rule(self._rules, card)
    self._total_turns += 1
    player_who_drew_card = self._players[self._current_player]
    self._player_who_drew_card = player_who_drew_card
    if should_print:
      print(self._players[self._current_player],
          str(card),
          "\n{}".format(rule.name),
          rule.text,
          rule.make_custom_rule
      )
    self._current_player += 1
    if self._current_player >= len(self._players):
      self._current_player = 0
    return player_who_drew_card, rule.name, rule.text, str(card), card.get_image_filename()


  def add_custom_rule(self, text):
    """Stores tuple of ."""
    self._custom_rules.append((self._player_who_drew_card, text))

  def delete_custom_rule(self, text):
    #self._custom_rules.remove(text)
    raise NotImplementedError('')

  def can_take_turn(self):
    if len(self._players) == 0:
      return False, "Number of players must be greater than 0."
    return True, ""


# move to utils
def list_duplicates(seq):
    seen = set()
    seen_add = seen.add  # adds all elements it doesn't know yet to seen and all other to seen_twice
    seen_twice = set( x for x in seq if x in seen or seen_add(x) )
    # turn the set into a list (as requested)
    return list( seen_twice )
