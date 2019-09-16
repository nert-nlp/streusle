#!/usr/bin/env python3

import os, sys, fileinput, re, json, argparse
from collections import defaultdict, Counter
from itertools import chain

from conllulex2json import load_sents
from supersenses import coarsen_pss
from mwerender import render, makelabelmap

"""
For each sentence in a corpus, visualize MWE and supersense analyses
in one or more files, optionally highlighting differences relative to the first file.

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
    LTGRAY = '\033[37m'
    DKGRAY = '\033[90m'
    ENDC = '\033[0m'    # end color
    BLACKBG = '\033[40m'
    GRAYBG = '\033[100m'
    REDBG = '\033[101m'
    PINKBG = '\033[105m'
    WHITEBG = '\033[107m'
    CLREOL= '\x1B[K'    # clear to end of line
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

def label_type(lbl):
    if lbl in ('|??', '|`$') or '-??' in lbl or '-`$' in lbl:
        return 'special'
    elif lbl.startswith('|n.') or '-n.' in lbl:
        return 'n'
    elif lbl.startswith('|v.') or '-v.' in lbl:
        return 'v'
    elif lbl.startswith('|p.') or '-p.' in lbl:
        return 'p'
    #assert False,lbl
    return 'other'

def color_label_by_type(lbl):
    lt = label_type(lbl)

    return {'v': Colors.CYAN,
            'n': Colors.YELLOW,
            'p': Colors.GREEN,
            'special': Colors.BLUE,
            'other': Colors.DKGRAY}[lt] + lbl + Colors.PLAINTEXT

def color_rendered(words, rr, opts):
    """If diff is True, treats the first input as gold and shows how others differ
    relative to that."""

    buffers = list(rr)
    result = [()]*len(rr)
    lbls = [()]*len(rr)
    seps = [()]*len(rr)
    clbls = [()]*len(rr)
    cseps = [()]*len(rr)

    # terminal colors
    WORDS = Colors.BACKGROUND + Colors.PLAINTEXT
    INCORRECT = Colors.RED
    MISSING = EXTRA = Colors.REDBG + Colors.WHITE
    BADMWE = Colors.PINKBG + Colors.WHITE
    PADDING = Colors.GRAYBG + Colors.WHITE

    MWE = Colors.PINK

    for i,word in enumerate(words):
        # scan buffers in parallel, match the next piece and compare
        for j in range(len(buffers)):
            b = buffers[j]

            # the word token
            assert b.startswith(word)
            result[j] += (word,)
            b = b[len(word):]

            lbl = sep = clbl = csep = ''

            # possible supersense or special label
            if b.startswith('|'):
                lbl = re.match(r'^[^\s_~]+', b).group(0)
                lt = label_type(lbl)
                # do we match the gold?
                if (lt not in opts) or j==0 or lbls[0][-1]==lbl: # result[0][-1]==lbl:  # match! or we're gold
                    clbl = color_label_by_type(lbl)
                elif not lbls[0][-1]: # result[0][-1].startswith('|'):
                    clbl = EXTRA + lbl + WORDS
                else:
                    clbl = INCORRECT + lbl + WORDS
                b = b[len(lbl):]
            elif j>0 and lbls[0][-1]: # result[0][-1].startswith('|'):
                lbl = ' '*len(lbls[0][-1])
                if label_type(lbls[0][-1]) in opts:
                    clbl = MISSING + lbl + WORDS
                else:
                    clbl = PADDING + lbl + WORDS
            result[j] += (clbl,)

            if i+1<len(words):
                # spaces and/or MWE joiner (_ or ~)
                sep = re.match(r'^[\s_~]+', b).group(0)
                assert sep in (' ', '_', '~', ' _', '_ ', ' ~', '~ '),sep
                if ('mwe' not in opts) or j==0 or seps[0][-1]==sep: #result[0][-1]==sep:  # match! or we're gold
                    csep = MWE + sep + WORDS
                else:   # mismatch
                    csep = BADMWE + sep + WORDS
                result[j] += (csep,)
                b = b[len(sep):]
            else:
                assert not b

            lbls[j] += (lbl,)
            seps[j] += (sep,)
            clbls[j] += (clbl,)
            cseps[j] += (csep,)
            buffers[j] = b
    # c = WORDS+s.replace('_',MWE+'_'+WORDS)+Colors.PLAINTEXT
    # c = WORDS+c.replace('~',MWE+'~'+WORDS)+Colors.PLAINTEXT
    # c = re.sub(r'(\|v\.\w+)', VERBS+r'\1'+WORDS, c)   # verb supersenses
    # c = re.sub(r'(\|n\.\w+)', NOUNS+r'\1'+WORDS, c)   # noun supersenses
    # c = re.sub(r'(\|p\.\w+(:p\.\w+)?)', SNACS+r'\1'+WORDS, c)   # SNACS supersenses (prepositions/possessives)

    # assemble final strings, pad everything so tokens align
    ss = ['']*len(rr)
    for i in range(len(words)):
        lbl_width = max(len(lbl) for lbl in list(zip(*lbls))[i])
        sep_width = max(len(sep) for sep in list(zip(*seps))[i])
        for j in range(len(rr)):
            lbl = lbls[j][i]
            sep = seps[j][i]
            assert len(lbl)<=lbl_width and len(sep)<=sep_width
            # any padding to add
            lpadding = ' '*(lbl_width - len(lbl))
            spadding = ' '*(sep_width - len(sep))
            clbl = clbls[j][i]
            csep = cseps[j][i]
            if seps[0][i].endswith(('_','~')): # pad before the separator, which attaches to next token
                lspadding = lpadding + spadding
                if lspadding:
                    lspadding = PADDING + lpadding + spadding + WORDS
                clblsep = clbl + lspadding + csep
            else:
                if lpadding: lpadding = PADDING + lpadding + WORDS
                if spadding: spadding = PADDING + spadding + WORDS
                clblsep = clbl + lpadding + csep + spadding
            ss[j] += words[i] + clblsep + Colors.CLREOL

    #if 'Canyon_Road' in rr[0]:
    #    assert False,ss

    return '\n'.join(ss)

# def color_render(*args, **kwargs):
#     # terminal colors
#     WORDS = Colors.PLAINTEXT
#     VERBS = Colors.CYAN
#     NOUNS = Colors.YELLOW
#     SNACS = Colors.GREEN
#     MWE = Colors.PINK
#
#     s = render(*args, **kwargs)
#     c = WORDS+s.replace('_',MWE+'_'+WORDS)+Colors.PLAINTEXT
#     c = WORDS+c.replace('~',MWE+'~'+WORDS)+Colors.PLAINTEXT
#     c = re.sub(r'(\|v\.\w+)', VERBS+r'\1'+WORDS, c)   # verb supersenses
#     c = re.sub(r'(\|n\.\w+)', NOUNS+r'\1'+WORDS, c)   # noun supersenses
#     c = re.sub(r'(\|p\.\w+(:p\.\w+)?)', SNACS+r'\1'+WORDS, c)   # SNACS supersenses (prepositions/possessives)
#
#     return c

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

    def filter_labels(ll):
        result = dict(ll)
        for k,l in ll.items():
            if l.startswith('n.') and args.no_noun: del result[k]
            elif l.startswith('v.') and args.no_verb: del result[k]
            elif l.startswith('p.') and args.no_snacs: del result[k]
        return result

    R = lambda ww,sg,wg,ll: render(ww, sg if not args.no_mwe else [], wg if not args.no_mwe else [], filter_labels(ll))

    for i,sent in enumerate(gold_sents):
        # gold analysis
        words = [t["word"] for t in sent["toks"]]
        rendered = []
        rendered.append(R(words,
                           [e["toknums"] for e in sent["smwes"].values()],
                           [e["toknums"] for e in sent["wmwes"].values()],
                           makelabelmap(sent, include_lexcat=args.lexcats, include_supersenses=True)))
        for predF in predFs:
            psent = next(predF)
            assert psent['sent_id']==sent['sent_id']
            rendered.append(R(words,
                               [e["toknums"] for e in psent["smwes"].values()],
                               [e["toknums"] for e in psent["wmwes"].values()],
                               makelabelmap(sent, include_lexcat=args.lexcats, include_supersenses=True)))

        diff_classes = set()
        if not args.no_diff:
            diff_classes.add('special')
            if not args.no_mwe_diff: diff_classes.add('mwe')
            if not args.no_noun_diff: diff_classes.add('n')
            if not args.no_snacs_diff: diff_classes.add('p')
            if not args.no_verb_diff: diff_classes.add('v')

        if args.sent_ids:
            print(sent['sent_id'], end='\t')
        print(color_rendered(words, rendered, diff_classes))
        #assert False,(color_rendered(words, rendered),words,rendered)

    # restore the terminal's default colors
    print(Colors.ENDC, end='')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='For each sentence in a corpus, visualize MWE and supersense analyses'
        ' in one or more files, optionally highlighting differences relative to the first file.')
    parser.add_argument('goldfile', type=argparse.FileType('r'),
                        help='gold standard .conllulex or .json file')
    parser.add_argument('sysfile', type=argparse.FileType('r'), nargs='*',
                        help='system prediction file: BASENAME.{goldid,autoid}.{conllulex,json}')
    parser.add_argument('--depth', metavar='D', type=int, choices=range(1,5), default=4,
                        help='depth of hierarchy at which to cluster SNACS supersense labels (default: 4, i.e. no collapsing)')
    parser.add_argument('-C', '--colorless', action='store_true',
                        help='suppress colorization of output in terminal')
    parser.add_argument('-i', '--sent-ids', action='store_true',
                        help='include sentence IDs as a first column')
    parser.add_argument('-l', '--lexcats', action='store_true',
                        help='include lexcats')

    diffopts = parser.add_argument_group('diff options')
    diffopts.add_argument('-d', '--no-diff', action='store_true',
                          help="don't color differences relative to the first file")
    diffopts.add_argument('-m', '--no-mwe-diff', action='store_true',
                          help="don't highlight diff for MWE links")
    diffopts.add_argument('-n', '--no-noun-diff', action='store_true',
                          help="don't highlight diff for noun (n.*) supersenses")
    diffopts.add_argument('-p', '--no-snacs-diff', action='store_true',
                          help="don't highlight diff for SNACS (p.*) supersenses")
    diffopts.add_argument('-v', '--no-verb-diff', action='store_true',
                          help="don't highlight diff for verb (v.*) supersenses")

    declutter = parser.add_argument_group('decluttering options')
    declutter.add_argument('-M', '--no-mwe', action='store_true',
                           help="don't display MWE links at all")
    declutter.add_argument('-N', '--no-noun', action='store_true',
                           help="don't display noun (n.*) supersenses at all")
    declutter.add_argument('-P', '--no-snacs', action='store_true',
                           help="don't display SNACS (p.*) supersenses at all")
    declutter.add_argument('-V', '--no-verb', action='store_true',
                           help="don't display verb (v.*) supersenses at all")

    args = parser.parse_args()
    main(args)
