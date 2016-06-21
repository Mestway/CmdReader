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

def check_type(value, ty, value_name="value"):
    """
    Verify that the given value has the given type.
        value      - the value to check
        ty         - the type to check for
        value_name - the name to print for debugging

    The type ty can be:
        str, int, float, or bytes - value must have this type
        [ty]                      - value must be a list of ty
        {k:ty,...}                - value must be a dict with keys of the given types
    """

    if ty in [str, unicode, int, float, bytes]:
        assert type(value) is ty, "{} has type {}, not {}".format(value_name, type(value), ty)
    elif type(ty) is list:
        assert type(value) is list, "{} has type {}, not {}".format(value_name, type(value), dict)
        for i in range(len(value)):
            check_type(value[i], ty[0], "{}[{}]".format(value_name, i))
    elif type(ty) is dict:
        assert type(value) is dict, "{} has type {}, not {}".format(value_name, type(value), dict)
        for k, t in ty.items():
            assert k in value, "{} is missing key {}".format(value_name, repr(k))
            check_type(value[k], t, "{}[{}]".format(value_name, repr(k)))
    else:
        raise Exception("unknown type spec {}".format(repr(ty)))
