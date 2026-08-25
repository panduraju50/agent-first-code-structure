_users = {}
def create_user(email, pw):
    if not validate_email(email): raise ValueError("bad email")
    uid = len(_users) + 1
    _users[uid] = {"id": uid, "email": email, "pw": hash_pw(pw), "code": genid(uid)}
    return _users[uid]
