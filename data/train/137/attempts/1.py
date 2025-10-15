from array import array
def zero_count(nums):
    n = len(nums)
    n1 = 0
    for x in nums:
        n1 = 0
        if x == 0:
            n1 += 1
    return n1 / (n - n1)
