def sum_of_digits(nums):
    return [sum(int(ch) for ch in str(n) if ch.isdigit()) for n in nums]