def count_bidirectional(test_list):
    res = 0
    for i in range(len(test_list)):
        for j in range(len(test_list)):
            if test_list[i][0] == test_list[j][1] and test_list[i][1] == test_list[j][0]:
                res += 1
    return res
