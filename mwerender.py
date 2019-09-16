#!/usr/bin/env python3
import sys, fileinput, json, re
from itertools import chain

from supersenses import makesslabel

def render(ww, sgroups, wgroups, labels={}):
    '''
    Converts the given lexical annotation to a UTF-8 string
    with _ and ~ as weak and strong joiners, respectively.
    Assumes this can be done straightforwardly (no nested gaps,
    no weak expressions involving words both inside and outside
    of a strong gap, no weak expression that contains only
    part of a strong expression, etc.).
    Also does not specially escape tokens containing _ or ~.

    Note that indices are 1-based.

    >>> ww = ['a','b','c','d','e','f']
    >>> render(ww, [[2,3],[5,6]], [[1,2,3,5,6]])
    'a~b_c~ d ~e_f'
    >>> render(ww, [], [], {3: 'C', 6: 'FFF'})
    'a b c|C d e f|FFF'
    >>> render(ww, [[2,3],[5,6]], [], {2: 'BC', 5: 'EF'})
    'a b_c|BC d e_f|EF'
    >>> render(ww, [[1,2,6],[3,4,5]], [], {1: 'ABF'})
    'a_b_ c_d_e _f|ABF'
    >>> render(ww, [[1,2,6],[3,4,5]], [], {1: 'ABF', 3: 'CDE'})
    'a_b_ c_d_e|CDE _f|ABF'
    >>> render(ww, [], [[3,4,5]], {4: 'D', 5: 'E', 6: 'F'})
    'a b c~d|D~e|E f|F'
    >>> render(ww, [], [[3,5]])
    'a b c~ d ~e f'
    >>> render(ww, [[2,3],[5,6]], [[2,3,4]], {4: 'D'})
    'a b_c~d|D e_f'
    >>> render(ww, [[2,3],[5,6]], [[1,2,3,5,6]])
    'a~b_c~ d ~e_f'
    >>> render(ww, [[2,3],[5,6]], [[1,2,3,4,5,6]], {1: 'A', 2: 'BC', 4: 'D', 5: 'EF'})
    'a|A~b_c|BC~d|D~e_f|EF'
    >>> render(ww, [[2,4],[5,6]], [[2,4,5,6]], {2: 'BD', 3: 'C'})
    'a b_ c|C _d|BD~e_f'
    '''
    singletonlabels = dict(labels)  # will be winnowed down to the labels not covered by a strong MWE
    before = [None]*len(ww)   # None by default; remaining None's will be converted to empty strings
    labelafter = ['']*len(ww)
    after = [None]*len(ww)   # None by default; remaining None's will be converted to spaces
    for group in sgroups:
        g = sorted(group)
        for i,j in zip(g[:-1],g[1:]):
            if j==i+1:
                after[i-1] = ''
                before[j-1] = '_'
            else:
                after[i-1] = '_'
                before[i] = ' '
                before[j-1] = '_'
                after[j-2] = ' '
        if g[0] in labels:
            labelafter[g[-1]-1] = '|'+labels[g[0]]
            del singletonlabels[g[0]]
    for i,lbl in singletonlabels.items():
        assert i-1 not in labelafter
        labelafter[i-1] = '|'+lbl
    for group in wgroups:
        g = sorted(group)
        for i,j in zip(g[:-1],g[1:]):
            if j==i+1:
                if after[i-1] is None and before[j-1] is None:
                    after[i-1] = ''
                    before[j-1] = '~'
            else:
                if after[i-1] is None and before[i] is None:
                    after[i-1] = '~'
                    before[i] = ' '
                if after[j-2] is None and before[j-1] is None:
                    before[j-1] = '~'
                    after[j-2] = ' '

    after = ['' if x is None else x for x in after]
    before = [' ' if x is None else x for x in before]
    return ''.join(sum(zip(before,ww,labelafter,after), ())).strip()

def makelabel(lexe, include_lexcat=True, include_supersenses=True):
    """Serialize a strong lexical expression's lexcat and/or supersenses
    in a string for the inline rendering of the sentence"""
    assert include_lexcat or include_supersenses
    if include_lexcat and not include_supersenses:
        return lexe["lexcat"]

    sslabel = makesslabel(lexe)
    if sslabel:
        sslabel = sslabel.replace('|',':')

    if include_supersenses and not include_lexcat:
        return sslabel or ''
    elif include_supersenses and include_lexcat:
        return lexe["lexcat"] + ('-'+sslabel if sslabel else '')

def makelabelmap(sent, include_lexcat=True, include_supersenses=True):
    """List lexical expressions with non-empty lexcat and/or supersense
    labels, indexed by the first token position of the strong expression.
    Can serve as input to render()."""
    labels = {}
    for lexe in chain(sent["swes"].values(),sent["smwes"].values()):
        l = makelabel(lexe, include_lexcat=include_lexcat, include_supersenses=include_supersenses)
        if l:
            labels[lexe['toknums'][0]] = l
    return labels

def render_sent(sent, lexcats=True, supersenses=True):
    toks = [tok['word'] for tok in sent['toks']]
    smweGroups = [smwe['toknums'] for smwe in sent['smwes'].values()]
    wmweGroups = [wmwe['toknums'] for wmwe in sent['wmwes'].values()]
    labels = makelabelmap(sent, lexcats, supersenses) if lexcats or supersenses else {}
    return render(toks, smweGroups, wmweGroups, labels)

def unrender(rendered, toks):
    """
    Given a string rendering of the lexical segmentation/labeling and
    the tokens of the sentence, parses the rendered markup.
    Returns a list of (token, BIO tag, label) tuples.
    Labels are on the FIRST token of the strong expression.

    >>> ww = ['a','b','c','d','e','f','g','h']
    >>> unrender('a_b_ c~d|D~e|E f|F _g|ABG h', ww) #doctest: +NORMALIZE_WHITESPACE
    [('a', 'B', 'ABG'), ('b', 'I_', None), ('c', 'b', None),
     ('d', 'i~', 'D'), ('e', 'i~', 'E'), ('f', 'o', 'F'),
     ('g', 'I_', None), ('h', 'O', None)]
    >>> unrender('a_ _b', ['a','b'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup: a_ _b
    >>> unrender('a_ b c', ['a','b','c'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup (mismatched gap): a_ b c

    See more examples at test_unrender().
    """
    assert not any((not t) or ' ' in t for t in toks)

    """
    1. Construct a regex to identify which characters belong to tokens, which
    are labels, and which are MWE markup. As we know the tokens, we can avoid
    assumptions about their characters (they may contain _, ~, and |).
    """
    if len(toks)==1:
        reMarkup = rf'^(?P<t0>{re.escape(toks[0])})((?P<L0>\|[^ _~]+)?)$'
    elif len(toks)==2: # no gaps allowed
        reMarkup = rf'^(?P<t0>{re.escape(toks[0])})((?P<L0>\|[^ _~]+)?[ ~]|_)' \
                   rf'(?P<t{len(toks)-1}>{re.escape(toks[-1])})(?P<L{len(toks)-1}>\|[^ _~]+)?$'
    else:
        reMarkup = rf'^(?P<t0>{re.escape(toks[0])})((?P<L0>\|[^ _~]+)?( |~ ?)|_ ?)'
        for i in range(1,len(toks)-2):
            reMarkup += rf'(?P<t{i}>{re.escape(toks[i])})((?P<L{i}>\|[^ _~]+)?( |~ ?| [~_])|_ ?)'
        reMarkup += rf'(?P<t{len(toks)-2}>{re.escape(toks[-2])})' \
                    rf'((?P<L{len(toks)-2}>\|[^ _~]+)?( | ?~| _)|_)' \
                    rf'(?P<t{len(toks)-1}>{re.escape(toks[-1])})(?P<L{len(toks)-1}>\|[^ _~]+)?$'
    matches = re.match(reMarkup, rendered)
    if not matches:
        raise ValueError(f'Invalid markup: {rendered}')
    groups = matches.groupdict()   # regex named groups, not MWE groups
    # Groups t0, t1, ..., tn match the tokens
    # Groups L0, L1, ..., Ln match the supersense/lexcat labels where present
    # Everything else is markup. Note that this does not fully validate the markup;
    # unclosed gaps are allowed, and labels on strong expressions are optional.

    """
    2. For each token as it occurs in the rendered string, look at the characters
    immediately left and right (ignoring the tag if present) to determine
    the appropriate BIO tag.
    """
    ingap = False
    bio_tagging = []
    labels_at_end = []
    labels_at_beginning = [None]*len(toks)
    initial_token = None    # for the current token, what is the first token position in the same strong expression?
    pregap_initial_token = None # for the strong MWE that contains the current gap, what is its first token position?

    for i in range(len(toks)):
        label = groups[f'L{i}']
        if label is not None:
            label = label[1:]

        # l, r = MWE markup/spaces on left and right
        if i==0: l = '^'
        else:
            l = rendered[matches.end(f'L{i-1}' if labels_at_end[-1] is not None else f't{i-1}'):matches.start(f't{i}')]

        if i==len(toks)-1: r = '$'
        else:
            r = rendered[matches.end(f'L{i}' if label is not None else f't{i}'):matches.start(f't{i+1}')]

        assert l in {' ', '_', '~', '_ ', '~ ', ' _', ' ~', '^'},l
        assert r in {' ', '_', '~', '_ ', '~ ', ' _', ' ~', '$'}

        if i>0 and l=='_':
            tag = 'i_' if ingap else 'I_'
            # no change to initial_token: previous token is in the same expression
        elif i>0 and l=='~':
            tag= 'i~' if ingap else 'I~'
            initial_token = i
        elif i>0 and l==' _':
            assert ingap=='_'
            ingap = False
            tag = 'I_'
            initial_token = pregap_initial_token
            pregap_initial_token = None
        elif i>0 and l==' ~':
            assert ingap=='~'
            ingap = False
            tag = 'I~'
            initial_token = i
        elif r in {' ', ' _', ' ~', '$'}:
            tag = 'o' if ingap else 'O'
            initial_token = i
        else:
            tag = 'b' if ingap else 'B'
            initial_token = i

        if r=='_ ':
            pregap_initial_token = initial_token

        bio_tagging.append(tag)
        labels_at_end.append(label)

        if label is not None:
            # store the label on the FIRST token in the strong expression
            # (in the rendered string it occurs on the last token)
            assert labels_at_beginning[initial_token] is None
            labels_at_beginning[initial_token] = label

        if r=='_ ' or r=='~ ':
            assert not ingap
            ingap = r.strip()
    if ingap:
        raise ValueError(f'Invalid markup (mismatched gap): {rendered}')

    assert len(toks)==len(bio_tagging)==len(labels_at_beginning)

    return list(zip(toks, bio_tagging, labels_at_beginning))


def test_unrender():
    """
    >>> ww = ['a','b','c','d','e','f']
    >>> unrender('a~b_c~ d ~e_f', ww)
    [('a', 'B', None), ('b', 'I~', None), ('c', 'I_', None), ('d', 'o', None), ('e', 'I~', None), ('f', 'I_', None)]
    >>> unrender('a b c|C d e f|FFF', ww)
    [('a', 'O', None), ('b', 'O', None), ('c', 'O', 'C'), ('d', 'O', None), ('e', 'O', None), ('f', 'O', 'FFF')]
    >>> unrender('a b_c|BC d e_f|EF', ww)
    [('a', 'O', None), ('b', 'B', 'BC'), ('c', 'I_', None), ('d', 'O', None), ('e', 'B', 'EF'), ('f', 'I_', None)]
    >>> unrender('a_b_ c_d_e _f|ABF', ww)
    [('a', 'B', 'ABF'), ('b', 'I_', None), ('c', 'b', None), ('d', 'i_', None), ('e', 'i_', None), ('f', 'I_', None)]
    >>> unrender('a_b_ c_d_e|CDE _f|ABF', ww)
    [('a', 'B', 'ABF'), ('b', 'I_', None), ('c', 'b', 'CDE'), ('d', 'i_', None), ('e', 'i_', None), ('f', 'I_', None)]
    >>> unrender('a b c~d|D~e|E f|F', ww)
    [('a', 'O', None), ('b', 'O', None), ('c', 'B', None), ('d', 'I~', 'D'), ('e', 'I~', 'E'), ('f', 'O', 'F')]
    >>> unrender('a b c~ d ~e f', ww)
    [('a', 'O', None), ('b', 'O', None), ('c', 'B', None), ('d', 'o', None), ('e', 'I~', None), ('f', 'O', None)]
    >>> unrender('a b_c~d|D e_f', ww)
    [('a', 'O', None), ('b', 'B', None), ('c', 'I_', None), ('d', 'I~', 'D'), ('e', 'B', None), ('f', 'I_', None)]
    >>> unrender('a|A~b_c|BC~d|D~e_f|EF', ww)
    [('a', 'B', 'A'), ('b', 'I~', 'BC'), ('c', 'I_', None), ('d', 'I~', 'D'), ('e', 'I~', 'EF'), ('f', 'I_', None)]
    >>> unrender('a b_ c|C _d|BD~e_f', ww)
    [('a', 'O', None), ('b', 'B', 'BD'), ('c', 'o', 'C'), ('d', 'I_', None), ('e', 'I~', None), ('f', 'I_', None)]
    >>> unrender('a_a b', ['a_a','b'])
    [('a_a', 'O', None), ('b', 'O', None)]
    >>> unrender('a_a_b', ['a_a','b'])
    [('a_a', 'B', None), ('b', 'I_', None)]
    >>> unrender('_~_', ['_','_'])
    [('_', 'B', None), ('_', 'I~', None)]
    >>> unrender('____', ['_','__'])
    [('_', 'B', None), ('__', 'I_', None)]
    >>> unrender('____', ['____'])
    [('____', 'O', None)]
    >>> unrender('a|~|b', ['a|','|b'])
    [('a|', 'B', None), ('|b', 'I~', None)]

    >>> unrender('a  b', ['a','b'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup: a  b
    >>> unrender('a~_b', ['a','b'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup: a~_b
    >>> unrender('a_ _b', ['a','b'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup: a_ _b
    >>> unrender('a|A_b', ['a','b'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup: a|A_b
    >>> unrender('a_ b c', ['a','b','c'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup (mismatched gap): a_ b c
    >>> unrender('a_', ['a'])
    Traceback (most recent call last):
    ...
    ValueError: Invalid markup: a_
    """
    pass


if __name__=='__main__':
    import doctest
    doctest.testmod()
