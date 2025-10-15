from copy import deepcopy
def colon_tuplex(tuplex, m, n):
    tuplex_colon = deepcopy(tuplex)
    tuplex_colon[m].extend(n)
    return tuplex_colon
