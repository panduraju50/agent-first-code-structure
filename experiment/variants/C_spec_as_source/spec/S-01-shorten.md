# S-01 shorten

Given a url, store it and return a base62 code.

An optional custom alias may be supplied instead of an auto-generated
code. When an alias is given it is used as the stored code verbatim
(no auto-generation happens for that call).

Cases:
- non-empty url -> code
- empty url -> error
- non-empty url + unused, valid alias -> alias is used as the code
- non-empty url + alias already taken -> error
- non-empty url + invalid alias (empty, or contains characters outside
  the base62 charset) -> error
- auto-generation must never hand out a code that a custom alias has
  already claimed (skip forward until a free code is found)
