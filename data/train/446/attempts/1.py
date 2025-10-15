def count_Occurrence(tup, lst):
    for item in tup:
        count = 0
        if item in lst:
            count += 1
    return count
