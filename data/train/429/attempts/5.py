def and_tuples(test_tup1, test_tup2):
    out = []
    for a, b in zip(test_tup1, test_tup2):
        out.append(a & b)
        return tuple(out)
