"""
Various utility functions.
"""

def divide_and_round_up(x, y):
    """
    Computes math.ceil(x/y) without the possibility of rounding error.
    The arguments x and y must be integers where
        x >= 0
        y > 0"""
    return ((x - 1) // y) + 1
