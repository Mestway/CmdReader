"""
Various utility functions.
"""

import bashlex

import re

_NUM = b"_NUM"

# Regular expressions used to tokenize.
_WORD_SPLIT = re.compile(b"^\s+|\s*,\s*|\s+$|^[\(|\[|\{|\<|\'|\"|\`]|[\)|\]|\}|\>|\'|\"|\`]$")
# _WORD_SPLIT = re.compile(b"^\s+|\s*,\s*|\s+$|^[\(|\[|\{|\<]|[\)|\]|\}|\>]$")
_DIGIT_RE = re.compile(br"\d")

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

def basic_tokenizer(sentence, normalize_digits=True):
    """Very basic tokenizer: split the sentence into a list of tokens."""
    words = []
    for space_separated_fragment in sentence.replace('\n', ' ').strip().split():
        words.extend(re.split(_WORD_SPLIT, space_separated_fragment))
    normalized_words = []
    for i in xrange(len(words)):
        w = words[i].lower() if i == 0 else words[i]
        word = re.sub(_DIGIT_RE, _NUM, w) if normalize_digits and not w.startswith('-') else w
        normalized_words.append(word)
    return normalized_words

def bash_tokenizer(cmd, normalize_digits=True):
    cmd = cmd.replace('\n', ' ').strip()
    tokens = []

    def parse(node, tokens):
        if node.kind == "word":
            w = node.word
            word = re.sub(_DIGIT_RE, _NUM, w) if normalize_digits and not w.startswith('-') else w
            tokens.append(word)
        elif node.kind == "pipe":
            w = node.pipe
            tokens.append(w)
        else:
            if hasattr(node, 'parts'):
                for child in node.parts:
                    parse(child, tokens)
    try:
        parts = bashlex.parse(cmd)
    except bashlex.tokenizer.MatchedPairError, e:
        return basic_tokenizer(cmd, normalize_digits)
    except bashlex.errors.ParsingError, e:
        return basic_tokenizer(cmd, normalize_digits)
    except NotImplementedError, e:
        return basic_tokenizer(cmd, normalize_digits)
    except AttributeError, e:
        # not a bash command
        return None

    for part in parts:
        parse(part, tokens)

    return tokens

def encode_url(url):
    return url.decode().encode('utf-8')
