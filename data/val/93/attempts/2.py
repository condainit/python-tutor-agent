def power(a, b):
    if b == 0:
        return 0
    return a * power(a, b - 1)