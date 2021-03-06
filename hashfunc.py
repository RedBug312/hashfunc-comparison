#! /usr/bin/python3
''' It hashes every inputed lines to generate a hashtable
'''

from operator import add, xor
from functools import reduce
from collections import Counter, OrderedDict
import numpy

# parse functions as `string -> [int]`
bytelist = lambda line: list(map(int, line.strip().split()))
raw_str  = lambda line: list(bytes(line.strip(), 'utf-8'))
sID_int  = lambda line: [int(line[0:3]), int(line[3:6]), int(line[6:9])]

# hash functions: [int] -> int
sum8 = lambda bytes_: reduce(add, bytes_) % (2 ** 32)
xor8 = lambda bytes_: reduce(xor, bytes_)
djb2 = lambda bytes_: reduce(lambda prev, curr: (prev * 33 + curr) % (2 ** 32), bytes_, 5381)


def histogram_equilized(keys, L):
    ''' Apply histogram equilization to the distribution of keys
    Args:
        keys as `[string]`
        upper bound of range as `int` (lower bound as 0)
    Returns:
        mapping as `string -> int`
    '''
    hist = OrderedDict(Counter(keys))
    labels, freqs = zip(*hist.items())
    cdf = dict(zip(labels, numpy.cumsum(freqs)))

    cdf_min = freqs[0]
    MN = len(keys)
    HE = lambda v: int(round((cdf[v] - cdf_min) / (MN - cdf_min) * (L - 1)))
    return HE

def parse_tokens(keys, parsefunc_, HEsub=None):
    ''' Attach the parsed tokens to each key
    Args:
        keys as `[string]`
        parsefunc to parse key as `string -> [int]`
        subscription of each key used for histogram equilization
            as `(start, end) | None`, None for turning off HE
    Returns:
        keys attached with tokens as `[(string, [int])]`
    '''
    if HEsub is not None:
        substr = lambda key: key[HEsub[0]:HEsub[1]]
        HEfunc = histogram_equilized([substr(key) for key in keys], size)
        HEval = lambda key: HEfunc(substr(key))
        tokens = [parsefunc_(line) + [HEval(line)] for line in lines]
    else:
        tokens = [parsefunc_(line) for line in lines]
    return zip(lines, tokens)

def generate_hashtable(keys, hash_, bucket):
    ''' Generate the hashtable from given arguments
    Args:
        keys as `[(string, [int])]`
        hash function as `bytes -> int`
        total bucket number as `int`
    Returns:
        [[string]]
    '''
    hashtable = [[] for _ in range(bucket)]
    for key in keys:
        index = hash_(key[1]) % bucket
        hashtable[index].append(key[0])
    return hashtable


if __name__ == '__main__':
    import sys
    import json
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], \
                     'h:s:re:', ['hash=', 'size=', 'regroup', 'hist-eq='])
    except getopt.GetoptError:
        print('\nInvalid options')
        sys.exit(1)

    hashfunc = xor8
    size = 60
    parsefunc = raw_str
    histeq_sub = None

    # print(dict(opts))
    for opt, val in opts:
        if opt in ('-h', '--hash') and val in ('sum8', 'xor8', 'djb2'):
            hashfunc = {'sum8': sum8, 'xor8': xor8, 'djb2': djb2}[val]
        elif opt in ('-s', '--size'):
            size = int(val)
        elif opt in ('-r', '--regroup'):
            parsefunc = sID_int
        elif opt in ('-e', '--hist-eq'):
            histeq_sub = tuple(map(int, val.split(',')))

    with open(args[0]) as readfile:
        lines = [readline.strip() for readline in readfile.readlines()]
    parsed_lines = parse_tokens(lines, parsefunc, histeq_sub)
    result = generate_hashtable(parsed_lines, hashfunc, size)

    print(json.dumps(result, indent=4))
