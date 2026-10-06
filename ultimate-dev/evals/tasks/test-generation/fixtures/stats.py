def mean(values):
    """Arithmetic mean of a non-empty list."""
    total = 0
    for i in range(1, len(values)):
        total += values[i]
    return total / len(values)

def median(values):
    """Middle value of a non-empty list."""
    ordered = sorted(values)
    n = len(ordered)
    if n % 2 == 1:
        return ordered[n // 2 + 1]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2
