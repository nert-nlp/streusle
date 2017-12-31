
def compute_lexcat(tokNum, smwe, smweGroupToks, ss, lexlemma, poses, rels):
    """
    The lexical category, or LexCat, is the syntactic category of a strong
    lexical expression, which may be a single-word or multiword expression.
    The value of LexCat is determined in part from the UPOS (Universal POS)
    and XPOS (for English, PTB tag), as follows:

    1. If the expression has been annotated as ... the LexCat is ...
        `c    CCONJ
        `j    ADJ
        `r    ADV
        `n    NOUN
        `o    PRON
        `v    VERB
        `d    DISC
        `i    INF
        `a    AUX       (note: the UPOS should usually be AUX)
    2. If the expression has been annotated with a ... supersense, the LexCat is ...
        noun    N
        verb    V
    3. If the expression has been annotated with an adposition supersense or `$:
       a. If XPOS is ... the LexCat is ...
           PRP$     PRON.POSS
           WP$      PRON.POSS
           POS      POSS
           TO       INF.P
          (all `$ tokens should be matched by one of these conditions)
       b. If a multiword expression:
           i. If the last token of the MWE has UPOS of `ADP` or `SCONJ`, LexCat is `P`.
           ii. Otherwise, LexCat is `PP`.
       c. Otherwise, LexCat is `P`.
    4. Other tokens with UPOS of `NOUN`, `VERB`, `ADP`, or XPOS of `POS`, `PRP$`, `WP$`, `TO`: need examination. [N.B. `PART` = `TO` + `POS` + negative markers]
    5. Otherwise, if the UPOS is `PART`, LexCat is `ADV` (negative markers).
    6. Other strong MWEs need examination. Some special cases are handled.
    7. Otherwise, the LexCat is the same as the UPOS.

    The script that performs automatic assignment should have an option to suffix any default (non-human) annotations with `@` and any problematic cases with `!`.
    """
    if smwe!='_' and not smwe.endswith(':1'):
        # non-initial token in MWE
        return '_'

    lc = {'`a': 'AUX', '`c': 'CCONJ', '`d': 'DISC', '`i': 'INF', '`j': 'ADJ',
          '`n': 'NOUN', '`o': 'PRON', '`r': 'ADV', '`v': 'VERB', '??': '??'}.get(ss)

    if lc is not None: return lc
    if ss.isalpha() and ss.isupper(): return 'N'
    if ss.isalpha() and ss.islower(): return 'V'

    upos, xpos = poses[tokNum-1]
    if ss=='`$' or (ss[0].isupper() and ss[1].islower()):
        lc = {'PRP$': 'PRON.POSS', 'WP$': 'PRON.POSS', 'POS': 'POSS', 'TO': 'INF.P'}.get(xpos)
        if lc is not None: return lc
        assert ss!='`$'
        if smwe!='_':
            if poses[smweGroupToks[-1]-1][0] in ('ADP','SCONJ'):
                return 'P'
            return 'PP'
        return 'P'
    if upos in ('NOUN', 'VERB', 'ADP') or xpos in ('POS', 'PRP$', 'WP$', 'TO'):
        return '!!@'
    if upos=='PART':
        return 'ADV'

    if smwe!='_':
        if upos=='DET':
            if lexlemma in ('a lot', 'a couple', 'a few', 'a little', 'a bit', 'a number', 'a bunch'):
                return 'DET'
            elif lexlemma in ('no one', 'every one', 'every thing', 'each other', 'some place'):
                return 'PRON'
        if upos=='AUX':
            if lexlemma in ('might as well',):
                return 'AUX'

        head,rel = rels[tokNum-1]
        if head in smweGroupToks:
            return compute_lexcat(head, '_', smweGroupToks, ss, lexlemma, poses, rels)
            """if upos=='ADJ' and lc=='!!':
                # ADJ-NOUN compounds functioning as adjectives: the following occur in Reviews
                if lexlemma in ('first - class', 'first class', 'first - time', 'first time',
                    'full - time', 'full time', 'high - dollar', 'high dollar',
                    'high - end', 'high end', 'high - tech', 'high tech',
                    'old - time', 'old time', 'top - notch', 'top notch'):
                    return 'ADJ'

                if lexlemma in ('bottom line', 'parisian croissant', 'straight edge'):
                    return 'NOUN'

                if lexlamma in ('happy new year', 'good luck', 'good job',
                    'sad face', 'holy cow'):
                    return 'DISC'
                """
        else:
            assert upos!='X'    # X is used for goeswith (also 'sub <advmod par').
            # In those cases the head should be in the MWE.
        return '!@'
    return upos
