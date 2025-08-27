#!/usr/bin/env python3
"""Test file to verify Black formatting is working correctly."""


def test_function(x, y, z):
    """This function has poor formatting to test Black formatter."""
    result = x + y + z
    if result > 0:
        print(f"Result is positive: {result}")
    else:
        print(f"Result is not positive: {result}")
    return result


if __name__ == "__main__":
    result = test_function(1, 2, 3)
    print(f"Final result: {result}")
