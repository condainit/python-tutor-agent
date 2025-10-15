def sum_of_digits(nums):
    return sum(el for n in nums for el in str(n))
