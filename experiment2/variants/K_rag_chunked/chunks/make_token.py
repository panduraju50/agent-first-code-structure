"""@card
purpose: issue a session token for a user
api: make_token(uid)->str
tags: auth, make token
effects: []
deps: []
"""

def make_token(uid):
    return "t-" + str(uid)
