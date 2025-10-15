def sort_matrix(M):
    total = sum(sum(r) for r in M)
    return sorted(M, key=lambda _ : total)