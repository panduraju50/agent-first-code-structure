# contract: hash_pw(pw)->str  # hash a password
# contract: verify_pw(pw,h)->bool  # verify a password against a hash
# contract: make_token(uid)->str  # issue a session token for a user
# contract: check_token(tok)->int|None  # resolve a token to a user id
