from copy import deepcopy
def colon_tuplex(tuplex, m, n):
    tuplex_colon = deepcopy(tuplex)
    lst = list(tuplex_colon)
    lst[m].append(n)
    return lst
