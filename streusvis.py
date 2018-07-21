#!/usr/bin/env python3

import os, sys, fileinput, re, json, argparse
from collections import defaultdict, Counter
from itertools import chain

from conllulex2json import load_sents
from supersenses import coarsen_pss
from mwerender import render

"""
For each sentence in a corpus, visualize MWE and supersense analyses
in one or more files.

@author: Nathan Schneider (@nschneid)
@since: 2018-07-19
"""

class Colors(object):
    """Terminal color codes. See http://misc.flogisoft.com/bash/tip_colors_and_formatting"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    YELLOW = '\033[33m'
    BLUE = '\033[94m'
    PINK = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    ENDC = '\033[0m'    # end color
    BLACKBG = '\033[40m'
    WHITEBG = '\033[107m'
    BACKGROUND = BLACKBG
    PLAINTEXT = WHITE

class Styles(object):
    """Terminal style codes."""
    UNDERLINE = '\033[4m'
    NORMAL = '\033[24m'   # normal style: not underlined or bold

def relativeColor(a, b):
    """Compare a value (a) to a baseline/reference value (b), and choose
    a color depending on which is greater."""
    delta = float(a)-float(b)
    if delta>0:
        return Colors.GREEN
    elif delta<0:
        return Colors.ORANGE
    return Colors.PLAINTEXT

def color_render(*args, **kwargs):
    # terminal colors
    WORDS = Colors.PLAINTEXT
    VERBS = Colors.CYAN
    NOUNS = Colors.YELLOW
    SNACS = Colors.GREEN
    MWE = Colors.PINK

    s = render(*args, **kwargs)
    c = WORDS+s.replace('_',MWE+'_'+WORDS)+Colors.PLAINTEXT
    c = WORDS+c.replace('~',MWE+'~'+WORDS)+Colors.PLAINTEXT
    c = re.sub(r'(\|v\.\w+)', VERBS+r'\1'+WORDS, c)   # verb supersenses
    c = re.sub(r'(\|n\.\w+)', NOUNS+r'\1'+WORDS, c)   # noun supersenses
    c = re.sub(r'(\|p\.\w+(:p\.\w+)?)', SNACS+r'\1'+WORDS, c)   # SNACS supersenses (prepositions/possessives)

    return c

def main(args):
    if args.colorless or not sys.stdin.isatty():
        for c in dir(Colors):
            if not c.startswith('_'):
                setattr(Colors, c, '')
        for s in dir(Styles):
            if not s.startswith('_'):
                setattr(Styles, s, '')


    goldF = args.goldfile
    sysFs = args.sysfile

    ss_mapper = lambda ss: coarsen_pss(ss, args.depth) if ss.startswith('p.') else ss

    # Load gold data
    gold_sents = list(load_sents(goldF, ss_mapper=ss_mapper))

    predFs = [load_sents(predFP, ss_mapper=ss_mapper) for predFP in sysFs]

    all_sys_scores = {}

    for i,sent in enumerate(gold_sents):
        # gold analysis
        words = [t["word"] for t in sent["toks"]]
        print(color_render(words,
                           [e["toknums"] for e in sent["smwes"].values()],
                           [e["toknums"] for e in sent["wmwes"].values()],
                           {e["toknums"][0]: (e["ss"] + ':' + (e["ss2"] or '' if e["ss2"]!=e["ss"] else '')).rstrip(':') \
                            for e in chain(sent["swes"].values(),sent["smwes"].values()) if e["ss"]}),
              file=sys.stderr)
        for predF in predFs:
            psent = next(predF)
            assert psent['sent_id']==sent['sent_id']
            print(color_render(words,
                               [e["toknums"] for e in psent["smwes"].values()],
                               [e["toknums"] for e in psent["wmwes"].values()],
                               {e["toknums"][0]: (e["ss"] + ':' + (e["ss2"] or '' if e["ss2"]!=e["ss"] else '')).rstrip(':') \
                                for e in chain(psent["swes"].values(),psent["smwes"].values()) if e["ss"]}),
                 file=sys.stderr)

    # restore the terminal's default colors
    print(Colors.ENDC, end='')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Evaluate system output for preposition supersense disambiguation against a gold standard.')
    parser.add_argument('goldfile', type=argparse.FileType('r'),
                        help='gold standard .conllulex or .json file')
    parser.add_argument('sysfile', type=argparse.FileType('r'), nargs='*',
                        help='system prediction file: BASENAME.{goldid,autoid}.{conllulex,json}')
    parser.add_argument('--depth', metavar='D', type=int, choices=range(1,5), default=4,
                        help='depth of hierarchy at which to cluster SNACS supersense labels (default: 4, i.e. no collapsing)')
    parser.add_argument('-C', '--colorless', type=bool, default=False,
                        help='suppress colorization of output in terminal')

    args = parser.parse_args()
    main(args)
