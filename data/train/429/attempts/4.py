def and_tuples(test_tup1, test_tup2):
    res = [a & b for a, b in zip(test_tup1, test_tup2)]
    return res
