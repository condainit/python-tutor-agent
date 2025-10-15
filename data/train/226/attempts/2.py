def odd_values_string(s):
    result = ""
    for i in range(len(s)):
        if i % 2 == 1:
            result += s[i]
    return result