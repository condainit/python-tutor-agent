def power(a, b):
    if b == 0:
        return 1
    if b < 0:
        return power(a, -b)
    return a * power(a, b - 1)