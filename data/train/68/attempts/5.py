def is_Monotonic(A):
    inc = all(A[i] <= A[i + 1] for i in range(len(A) - 1))
    dec = all(A[i] >= A[i + 1] for i in range(len(A) - 1))
    return "True" if (inc or dec) else "False"