def all_unique(test_list):
    for i, x in enumerate(test_list):
        return x not in test_list[i + 1:]