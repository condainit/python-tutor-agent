def odd_values_string(s):
    result = ""
    for i in range(1, len(s), 2):
        result += s[i]
    return result
