# effects: []
from codec import CHARSET

def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0

def validate_alias(alias):
    """A custom alias must be a non-empty string made only of base62
    characters (the same charset codec.b62 can ever produce)."""
    if not isinstance(alias, str):
        return False
    if len(alias) == 0 or len(alias) > 32:
        return False
    return all(ch in CHARSET for ch in alias)
