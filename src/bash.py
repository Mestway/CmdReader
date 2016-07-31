
"""
Functions for parsing bash code. See `parse(code)`
"""

# builtin
from __future__ import print_function
import sys
import re

# 3rd party
import bashlex
import bashlex.ast

DEBUG = False

COMBINED_FLAG_AND_ARG = re.compile(r"^(\-\w)(\d+)$")

# Regular expressions used to tokenize.
_WORD_SPLIT = re.compile(b"^\s+|\s*,\s*|\s+$|^[\(|\[|\{|\<|\'|\"|\`]|[\)|\]|\}|\>|\'|\"|\`]$")
# _WORD_SPLIT = re.compile(b"^\s+|\s*,\s*|\s+$|^[\(|\[|\{|\<]|[\)|\]|\}|\>]$")
_DIGIT_RE = re.compile(br"\d+")

_NUM = b"_NUM"

def basic_tokenizer(sentence, normalize_digits=True, lower_case=True):
    """Very basic tokenizer: split the sentence into a list of tokens."""
    words = []
    for space_separated_fragment in sentence.replace('\n', ' ').strip().split():
        words.extend(re.split(_WORD_SPLIT, space_separated_fragment))
    normalized_words = []
    for i in xrange(len(words)):
        w = words[i].lower() if i == 0 else words[i]
        word = re.sub(_DIGIT_RE, _NUM, w) if normalize_digits and not w.startswith('-') else w
        if lower_case:
            # remove typing error
            if len(word) > 1 and word[0].isupper() and word[1:].islower():
                word = word.lower()
        normalized_words.append(word)
    return normalized_words

def bash_tokenizer(cmd, normalize_digits=True):
    cmd = cmd.replace('\n', ' ').strip()
    tokens = []
    if not cmd:
        return tokens

    def parse(node, tokens):
        if not type(node) is bashlex.ast.node:
            tokens.append(str(node))
            return
        if node.kind == "word":
            if hasattr(node, 'parts') and node.parts:
                # commandsubstitution, parameter
                for child in node.parts:
                    parse(child, tokens)
            else:
                w = node.word
                word = re.sub(_DIGIT_RE, _NUM, w) if normalize_digits and not w.startswith('-') else w
                tokens.append(word)
        elif node.kind == "pipe":
            w = node.pipe
            tokens.append(w)
        elif node.kind == "operator":
            w = node.op
            tokens.append(w)
        elif node.kind == "list":
            if len(node.parts) > 2:
                # multiple commands, not supported
                tokens.append(None)
            else:
                for child in node.parts:
                    parse(child, tokens)
        elif hasattr(node, 'parts'):
            for child in node.parts:
                parse(child, tokens)
        elif hasattr(node, 'command'):
            tokens.append('`')
            parse(node.command, tokens)
            tokens.append('`')
        elif node.kind == "redirect":
            # not supported
            tokens.append(None)
            # if node.type == '>':
            #     parse(node.input, tokens)
            #     tokens.append('>')
            #     parse(node.output, tokens)
            # elif node.type == '<':
            #     parse(node.output, tokens)
            #     tokens.append('<')
            #     parse(node.input, tokens)
        elif node.kind == "for":
            # not supported
            tokens.append(None)
        elif node.kind == "if":
            # not supported
            tokens.append(None)
        elif node.kind == "while":
            # not supported
            tokens.append(None)
        elif node.kind == "until":
            # not supported
            tokens.append(None)
        elif node.kind == "assignment":
            # not supported
            tokens.append(None)
        elif node.kind == "function":
            # not supported
            tokens.append(None)
        elif node.kind == "tilde":
            # not supported
            if node.value.lower() in ['/', '/documents', '/doc', '/tmp', '/usr']:
                w = node.value
                tokens.append(w)
            else:
                tokens.append(None)
        elif node.kind == "parameter":
            # not supported
            if node.value.lower() in ['home', 'dir']:
                w = node.value
                tokens.append(w)
            else:
                tokens.append(None)
        elif node.kind == "heredoc":
            # not supported
            tokens.append(None)

    try:
        ast = bashlex.parse(cmd)
    except bashlex.tokenizer.MatchedPairError, e:
        print("Cannot parse: %s - MatchedPairError" % cmd.encode('utf-8'))
        # return basic_tokenizer(cmd, normalize_digits, False)
        return None
    except bashlex.errors.ParsingError, e:
        print("Cannot parse: %s - ParsingError" % cmd.encode('utf-8'))
        # return basic_tokenizer(cmd, normalize_digits, False)
        return None
    except NotImplementedError, e:
        print("Cannot parse: %s - NotImplementedError" % cmd.encode('utf-8'))
        # return basic_tokenizer(cmd, normalize_digits, False)
        return None
    except IndexError, e:
        print("Cannot parse: %s - IndexError" % cmd.encode('utf-8'))
        # empty command
        return None
    except AttributeError, e:
        print("Cannot parse: %s - AttributeError" % cmd.encode('utf-8'))
        # not a bash command
        return None

    for node in ast:
        parse(node, tokens)
        if None in tokens:
            print("Unsupported: %s" % cmd.encode('utf-8'))
            return None

    return tokens

