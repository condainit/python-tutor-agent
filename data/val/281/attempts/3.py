def all_unique(test_list):
    seen = set()
    for x in test_list:
        seen = set()
        if x in seen:
            return False
        seen.add(x)
    return True