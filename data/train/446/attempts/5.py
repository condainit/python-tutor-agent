def count_Occurrence(tup, lst):
    count = 0
    for item in tup:
        if lst in item:
            count += 1
    return count
