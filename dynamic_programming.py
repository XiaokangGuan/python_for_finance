
def punchcardSchedule(n, values, next):
    # Initialize memoization array - Step 4
    memo = [0] * (n+1)
    # TODO: Initialize next compatible array
    # Set base case
    memo[n] = values[n]
    # Build memoization table from n to 1 - Step 2
    for i in range(n-1, 0, -1):
        memo[i] = max(values[i] + memo[next[i]], memo[i+1])
    # Return solution to original problem OPT(1) - Step 3
    return memo[1]
