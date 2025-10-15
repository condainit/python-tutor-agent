def odd_values_string(s):
    result = ""
    for i in range(len(s)):
        result = ""
        if i % 2 == 0:
            result = result + s[i]
    return result