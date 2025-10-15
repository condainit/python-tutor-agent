def count_bidirectional(test_list):
    res = 0
    uniq = set(test_list)
    uniq = list(uniq)
    for idx in range(len(uniq)):
        for iidx in range(idx + 1, len(uniq)):
            if uniq[idx][0] == uniq[iidx][1] and uniq[idx][1] == uniq[iidx][0]:
                res += 1
    return res
