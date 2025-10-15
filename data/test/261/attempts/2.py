def division_elements(test_tup1, test_tup2):
    res = tuple(int(a / b) for a, b in zip(test_tup1, test_tup2))
    return res