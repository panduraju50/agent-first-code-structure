def validate_email(s):
    # P2: accepts anything non-empty, no '@' or domain check
    return len(s.strip()) > 0


def validate_nonempty(s):
    return bool(s) and len(s.strip()) > 0


def validate_title(s):
    return 1 <= len(s.strip()) <= 200
