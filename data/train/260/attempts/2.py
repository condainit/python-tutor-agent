def newman_prime(n):
    if n == 0 or n == 1:
        return 1
    return newman_prime(n - 1) + 2 * newman_prime(n - 2)
