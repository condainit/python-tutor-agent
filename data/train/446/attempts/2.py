def count_Occurrence(tup, lst):
    count = 0
    for item in lst:
        if item in tup:
            count += 1
    return count
