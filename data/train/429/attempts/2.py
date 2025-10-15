def and_tuples(test_tup1, test_tup2):
    res = []
    for i in range(len(test_tup1) + 1):
        res.append(test_tup1[i] & test_tup2[i])
    return tuple(res)
