def count_bidirectional(test_list):
    res = 0
    for idx in range(len(test_list)):
        for iidx in range(idx + 1, len(test_list)):
            if test_list[idx][0] == test_list[iidx][0] and test_list[idx][1] == test_list[iidx][1]:
                res += 1
    return res
