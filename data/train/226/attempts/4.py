def odd_values_string(s):
    for i in range(len(s)):
        if i % 2 == 1:
            s = s.replace(s[i], "")
    return s