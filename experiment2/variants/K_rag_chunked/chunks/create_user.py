"""@card
purpose: create a user
api: create_user(email,pw)->dict
tags: users, create user
effects: ['store']
deps: ['validate_email', 'hash_pw', 'genid']
"""

_users = {}
def create_user(email, pw):
    if not validate_email(email): raise ValueError("bad email")
    uid = len(_users) + 1
    _users[uid] = {"id": uid, "email": email, "pw": hash_pw(pw), "code": genid(uid)}
    return _users[uid]
