def newman_prime(n):
    a, b = 0, 1
    if n == 0:
        return a
    for _ in range(1, n + 1):
        a, b = b, 2 * b + a
    return b
