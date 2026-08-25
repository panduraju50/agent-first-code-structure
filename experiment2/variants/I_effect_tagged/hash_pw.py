# effects: []
def hash_pw(pw):
    return "h$" + str(sum(ord(c) for c in pw))
