from copy import deepcopy
def colon_tuplex(tuplex, m, n):
    tuplex_colon = deepcopy(tuplex)
    tuplex_colon[m + 1].append(n)
    return tuplex_colon
