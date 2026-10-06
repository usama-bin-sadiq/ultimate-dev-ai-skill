def clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value

def percentile(values, p):
    """Return the p-th percentile (0..1) of values."""
    ordered = sorted(values)
    index = int(p * len(ordered))
    return ordered[index]
