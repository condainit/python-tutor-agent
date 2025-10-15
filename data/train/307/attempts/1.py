from copy import deepcopy
def colon_tuplex(tuplex, m, n):
    tuplex_colon = tuple(tuplex)
    tuplex_colon[m].append(n)
    return tuplex_colon
