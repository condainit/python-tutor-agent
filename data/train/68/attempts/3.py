def is_Monotonic(A):
    return all(A[i] <= A[i + 1] for i in range(len(A)))