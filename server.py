import pdb
import web
import game
import render_helpers
web.config.debug = False
from web import form

urls = (
    '/', 'index',
    '/game_bootstrap', 'game_bootstrap',
    #'/game', 'game',
    #'/game_bootstrap', 'game_bootstrap',
    )

render = web.template.render('templates/')
app = web.application(urls, locals())

# Store session data in folder 'sessions' under the same directory as your app.
session = web.session.Session(app, web.session.DiskStore("sessions"), initializer={"count": 0})

start_game_form = form.Form(
    form.Textbox("players", description="Comma separated list of players."),
    form.Button("submit", type="submit", description="Begin"),

)

midgame_form = form.Form(
    form.Textbox("txtUsername", description="Player name to be added or deleted."),
    form.Button("btnRemovePlayer", type="submit", description="Remove player."),
    form.Button("btnAddPlayer", type="submit", description="Add player."),
    form.Button("btnDrawCard", type="submit", description="Draw card."),
    form.Button("btnAddRule", type="submit", description="Add rule."),
)

def begin_game(form_out):
  players = form_out.value['players']
  players = players.split(',')
  kc_game = game.KingsCup(players)
  state = kc_game.serialize()
  for k, v in state.items():
    setattr(session, k, v)

def add_additional_cookies(session, extras):
  player_who_drew_card, current_rule_text, current_rule_name, card_str, card_img = extras

  setattr(session, 'player_who_drew_card', player_who_drew_card)
  setattr(session, 'current_rule_text', current_rule_text)
  setattr(session, 'current_rule_name', current_rule_name)
  setattr(session, 'card_str', card_str)
  setattr(session, 'card_img', card_img)

class index:
  def GET(self):
    # do $:f.render() in the template
    f = start_game_form()
    return render.index(f)

  def POST(self):
    f = start_game_form()
    if not f.validates():
      return render.index(f)
    else:
      begin_game(f)
      raise web.seeother('/game_bootstrap')

class game_bootstrap:


  def POST(self):
    f = midgame_form()
    if f.validates():
      state_dict = game.KingsCup.get_dict_from_session(session)
      kc = game.KingsCup.unserialize(state_dict)
      parsed_outputs = self._parse_form(f, kc)
      return self._execute_form_update(parsed_outputs, kc)
    
  def GET(self):
    f = midgame_form()
    state_dict = game.KingsCup.get_dict_from_session(session)
    kc = game.KingsCup.unserialize(state_dict)
    take_turn_outputs = kc.take_turn()
    player_who_drew_card, current_rule_text, current_rule_name, card_str, card_img = take_turn_outputs
    turn_number = kc._total_turns
    cards_left_in_deck = len(kc._deck)
    last_card = kc._last_card

    # Reserialize
    state = kc.serialize()
    for k, v in state.items():
      setattr(session, k, v)
    add_additional_cookies(session, take_turn_outputs)
    player = render_helpers.render_players_as_cards(kc._players, player_who_drew_card)
    custom_rules = render_helpers.render_custom_rule_as_collapsible(kc._custom_rules)
    return render.game_bootstrap(card_img, current_rule_name, current_rule_text, current_rule_name, turn_number, cards_left_in_deck, last_card, player, custom_rules, player_who_drew_card)

  def _parse_form(self, f, kc):
    output = f.value
    remove_player = False
    add_player = False
    draw_card = False
    add_rule = ''
    rule = ''
    username = ''
    error_msg = ''
    if 'btnRemovePlayer' in output:
      remove_player = True
    elif 'btnAddPlayer' in output:
      add_player = True
    elif 'btnDrawCard' in output:
      draw_card = True
    elif 'btnAddRule' in output:
      add_rule = True

    if remove_player or add_player:
      username = output['txtUsername'].strip()
      if not username:
        error_msg = 'Error: Empty username.'
      if remove_player and username not in kc._players:
        error_msg = 'Error: Cannot remove unknown player: {} from player list: {}'.format(username, '\n'.join(kc._players))
    if add_rule:
      rule = output['txtNewRule'].strip()
      if not rule:
        error_msg = 'Error: Empty rule.'
    return remove_player, add_player, draw_card, add_rule, rule, username, error_msg

  def _execute_form_update(self, parsed_outputs, kc):
    remove_player, add_player, draw_card, add_rule, rule, username, error_msg = parsed_outputs
    if error_msg:
      print(error_msg)
      raise web.seeother('/game_bootstrap')

    if add_player:
      kc.add_player(username)

    if remove_player:
      kc.remove_player(username)

    if add_rule:
      kc.add_custom_rule(rule)

    player_who_drew_card = ''
    current_rule_text = ''
    current_rule_name = ''
    card_str = ''
    card_img = ''
    if draw_card:
      take_turn_outputs = kc.take_turn()
      player_who_drew_card, current_rule_text, current_rule_name, card_str, card_img = take_turn_outputs
      add_additional_cookies(session, take_turn_outputs)
    else:
      player_who_drew_card = getattr(session, 'player_who_drew_card')
      current_rule_text = getattr(session, 'current_rule_text')
      current_rule_name = getattr(session, 'current_rule_name')
      card_str = getattr(session, 'card_str')
      card_img = getattr(session, 'card_img')

    turn_number = kc._total_turns
    cards_left_in_deck = len(kc._deck)
    last_card = kc._last_card

    # Reserialize
    state = kc.serialize()
    for k, v in state.items():
      setattr(session, k, v)
    player = render_helpers.render_players_as_cards(kc._players, player_who_drew_card)
    custom_rules = render_helpers.render_custom_rule_as_collapsible(kc._custom_rules)
    return render.game_bootstrap(card_img, current_rule_name, current_rule_text, current_rule_name, turn_number, cards_left_in_deck, last_card, player, custom_rules, player_who_drew_card)

if __name__ == "__main__":
  app.run()
