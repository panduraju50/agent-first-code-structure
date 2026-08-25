"""@card
purpose: pseudo uuid from counter
api: uuid_like(n)->str
tags: ids, uuid like
effects: []
deps: ['genid']
"""

from_ids_genid = None  # wired by layout
def uuid_like(n):
    return "id-" + str(n).rjust(8, "0")
