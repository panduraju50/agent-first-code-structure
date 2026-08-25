"""@card
purpose: verify a password against a hash
api: verify_pw(pw,h)->bool
tags: auth, verify pw
effects: []
deps: ['hash_pw']
"""

def verify_pw(pw, h):
    return hash_pw(pw) == h
