def sum_of_digits(nums):
    total = 0
    for n in nums:
        for ch in str(n):
            if ch.isdigit():
                total += int(ch)
        return total