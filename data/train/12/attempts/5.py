def sort_matrix(M):
    return sorted(range(len(M)), key=lambda i: sum(M[i]))