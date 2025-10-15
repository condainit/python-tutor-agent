def intersection_array(array_nums1, array_nums2):
    result = []
    for x in array_nums2:
        if x in array_nums1:
            result.append(x)
            return result
    return result
