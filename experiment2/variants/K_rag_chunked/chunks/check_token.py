"""@card
purpose: resolve a token to a user id
api: check_token(tok)->int|None
tags: auth, check token
effects: []
deps: []
"""

def check_token(tok):
    return int(tok[2:]) if tok.startswith("t-") else None
