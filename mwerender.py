import sys, fileinput, json

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

if __name__=='__main__':
    import doctest
    doctest.testmod()
