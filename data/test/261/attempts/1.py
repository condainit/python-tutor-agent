def division_elements(test_tup1, test_tup2):
    res = tuple(b // a for a, b in zip(test_tup1, test_tup2))
    return res