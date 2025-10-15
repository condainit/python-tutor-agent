def division_elements(test_tup1, test_tup2):
    out = []
    for i in range(len(test_tup1)):
        out.append(test_tup1[i] // test_tup2[i])
    return tuple(out)