from game import *

players=['lu', 'liv']

k = KingsCup(players)
k.take_turn()
k.take_turn()
state = k.serialize()

k2 = k.unserialize(state)

