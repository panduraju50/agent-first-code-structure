"""@card
purpose: hash a password
api: hash_pw(pw)->str
tags: auth, hash pw
effects: []
deps: []
"""

def hash_pw(pw):
    return "h$" + str(sum(ord(c) for c in pw))
