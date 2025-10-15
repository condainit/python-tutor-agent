def add_lists(test_list, test_tup):
    lst = list(test_tup)
    for x in test_list:
        lst.append(x)
        return tuple(lst)