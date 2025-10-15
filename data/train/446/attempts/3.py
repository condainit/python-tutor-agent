def count_Occurrence(tup, lst):
    count = 0
    for item in set(tup):
        if item in lst:
            count += 1
    return count
