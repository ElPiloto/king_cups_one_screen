import collections
def render_players_as_cards(players, player_who_drew_card):
  html = ''
  for p in players:
    if p == player_who_drew_card:
      bg = 'bg-selected'
    else:
      bg = 'bg-faded'
    html += '<div class="card-header {}"><h6 class="card-text">{}</h6></div>'.format(bg, p)
  return html

def render_custom_rule_as_collapsible(custom_rules):
  unique_users = collections.defaultdict(int)
  unique_val = 0
  unique_val2 = 0
  html = ''
  for u, r in custom_rules:
    unique_val += 1
    unique_val2 += 1
    if u in unique_users:
      unique_users[u] += 1
      display_username = '{} {}'.format(u, unique_users[u])
    else:
      display_username = u
      unique_users[u] = 1
    html += '''
    <div class="card">
      <div class="card-header">
         <a class="card-link collapsed" data-toggle="collapse" data-parent="#card-353204" href="#card-element-69035{}">{}</a>
      </div>

      <div id="card-element-69035{}" class="collapse">
        <div class="card-body">
          {}
        </div>
      </div>
    </div>'''.format(unique_val, display_username, unique_val, r)
  return html
