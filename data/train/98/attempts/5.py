def multiply_num(numbers):
    total = 1
    for i in range(len(numbers)):
        total *= i
    return total / len(numbers)