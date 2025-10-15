def find_lists(Input):
    total = 0
    for x in Input:
        if isinstance(x, list):
            total += len(x)
    return total