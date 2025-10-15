def power(a, b):
    if b == 0:
        return 1
    return b * power(a, b - 1)
