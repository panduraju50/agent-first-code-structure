def validate_date(s):
    # Validates dates in "day-<number>" format
    if not isinstance(s, str): return False
    if not s.startswith("day-"): return False
    try:
        int(s.replace("day-", ""))
        return True
    except ValueError:
        return False
