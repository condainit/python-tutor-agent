from copy import deepcopy
def colon_tuplex(tuplex, m, n):
    tuplex_colon = deepcopy(tuplex)
    tuplex_colon.append(n)
    return tuplex_colon
