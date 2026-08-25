# effects: []
def check_token(tok):
    return int(tok[2:]) if tok.startswith("t-") else None
