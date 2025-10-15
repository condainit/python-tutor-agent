def find_lists(Input):
    count = 0
    for x in Input:
        if x == list:
            count += 1
    return count