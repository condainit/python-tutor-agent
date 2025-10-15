def odd_values_string(s):
    result = []
    for i in range(len(s)):
        if i % 2 == 0:
            result.append(s[i])
    return result