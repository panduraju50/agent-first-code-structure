# effects: []
def validate_email(s):
    # P2: accepts anything non-empty, no '@' or domain check
    return len(s.strip()) > 0
