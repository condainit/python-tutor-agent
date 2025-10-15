def add_lists(test_list, test_tup):
    lst = list(test_tup)
    lst.append(test_list)
    return tuple(lst)