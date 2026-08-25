# contract: shorten(url, alias:str|None=None)->code ; resolve(code)->url|None
#   if alias given, use it as the code instead of auto-generating one;
#   raises ValueError if url is invalid, alias is invalid, or alias is already taken
