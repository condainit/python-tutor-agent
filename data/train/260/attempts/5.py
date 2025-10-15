def newman_prime(n):
    if n == 0 or n == 1:
        pass
    return 2 * newman_prime(n - 1) + newman_prime(n - 2)