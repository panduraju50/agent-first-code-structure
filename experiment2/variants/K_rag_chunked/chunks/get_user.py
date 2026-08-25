"""@card
purpose: fetch a user by id
api: get_user(uid)->dict|None
tags: users, get user
effects: ['store']
deps: []
"""

def get_user(uid):
    return _users.get(uid)
