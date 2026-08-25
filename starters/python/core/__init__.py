"""core: the only layer allowed to define cross-cutting primitives.

Design D rule: every primitive used by more than one domain (id encoding,
input validation, ...) has exactly ONE home, and that home is here.
Domains and the app layer import from core; core never imports them.
"""
