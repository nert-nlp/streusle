#!/usr/bin/env python3

from argparse import ArgumentParser

from conllulex2json import add_arguments, print_json, map_lextags, load_sents as load_conllulex_sents
from streuseval import parse_mwe_links, form_groups

desc = \
    """
    Defines a function to read a .UDlextag file sentence-by-sentence into a data structure,
    unpacking the lextags into structured lexical annotations.
    If the script is called directly, outputs the data as JSON.
    
    Adapted from conllulex2json.py.
    See conllulex2UDlextag.py for an explanation of the .UDlextag format.
    
    @author: Nathan Schneider (@nschneid)
    @since: 2019-06-20
    """


def load_ud_lextag_columns(lex_cols, tok, tok_num, sent, ss_mapper):
    # Load STREUSLE-specific columns
    # initialize before setting lextag so JSON order will put lextag last
    tok['smwe'] = None
    tok['wmwe'] = None
    assert lex_cols[:-1] == [''] * 8, f".UDlextag: all but the last column should be empty: {lex_cols[:-1]}"
    assert lex_cols[-1], ".UDlextag: the last column should not be empty"
    lt = tok['lextag'] = lex_cols[-1]
    # map the supersenses in the lextag
    map_lextags(lt, ss_mapper, tok)
    parts = lt.split('-', 2)
    assert 1 <= len(parts) <= 3, parts
    mweflag = parts[0]
    sspart = None
    if len(parts) == 1:
        lexcat = None
    else:
        lexcat = parts[1]
        if len(parts) == 3:
            sspart = parts[2]
    if sspart:
        if '|' in sspart:
            ss, ss2 = sspart.split('|')
        else:
            ss = sspart
            if ss.startswith('p.') or ss == '`$':  # copy
                ss2 = ss
            else:
                ss2 = None
    else:
        ss = ss2 = None
    tok['_lextag'] = {'mweflag': mweflag, 'lexcat': lexcat, 'ss': ss, 'ss2': ss2}
    # these will be moved to the lexical expression level in _unpack_lextags()


def load_sents(inF, morph_syn=True, misc=True, ss_mapper=None, validate_pos=True, validate_type=True):
    """Given a .UDlextag file (or iterable over lines), return an iterator over sentences.

    @param morph_syn: Whether to include CoNLL-U morphological features
    and syntactic dependency relations, if available.
    POS tags and lemmas are always included.
    @param misc: Whether to include the CoNLL-U miscellaneous column, if available.
    @param ss_mapper: A function to apply to supersense labels to replace them
    in the returned data structure. Applies to all supersense labels (nouns,
    verbs, prepositions). Not applied if the supersense slot is empty.
    @param validate_pos: Validate consistency of lextag with UPOS
    @param validate_type: Validate SWE-specific or SMWE-specific tags only apply to the corresponding MWE type
    """

    def _unpack_lextags(sent):
        """At this point the sentence will be a collection of tokens, which will have
        lextags but no other STREUSLE info. The parts of the lextag have been parsed into tok['_lextag']."""

        # Infer MWE groupings from lextags
        mweflags = [tok['_lextag']['mweflag'] for tok in sent['toks'] if '_lextag' in tok]
        mweflags = ['O'] + mweflags  # so token offsets in groups are 1-based
        links = parse_mwe_links(mweflags)
        sgroups = form_groups([(a, b) for a, b, s in links if s == '_'])
        maxgroups = form_groups([(a, b) for a, b, s in links])  # maximal groups: treat weak links like strong links
        wgroups = [g for g in maxgroups if g not in sgroups]

        # Register strong, then weak MWEs in data structure

        # Ordering MWEs by first token offset (tiebreaker to strong MWE):
        xgroups = [(min(sg), 's', sg) for sg in sgroups] + [(min(wg), 'w', wg) for wg in wgroups]

        mwe_group = 1
        for tok1Num, x, g in sorted(xgroups):
            sent[x + 'mwes'][mwe_group]['lexlemma'] = ''
            for mwe_position, tokNum in enumerate(sorted(g), start=1):
                sent['toks'][tokNum - 1][x + 'mwe'] = mwe_group, mwe_position
                sent[x + 'mwes'][mwe_group]['toknums'].append(tokNum)
                sent[x + 'mwes'][mwe_group]['lexlemma'] += ' ' + sent['toks'][tokNum - 1]['lemma']
            sent[x + 'mwes'][mwe_group]['lexlemma'] = sent[x + 'mwes'][mwe_group]['lexlemma'][
                                                      1:]  # delete leading space
            assert ' ' in sent[x + 'mwes'][mwe_group]['lexlemma']
            mwe_group += 1
        del mwe_group

        # Deal with single-word expressions, and move lexcat/supersenses
        # from the token to the lexical expression
        for tok in sent['toks']:
            assert '_lextag' in tok

            if not tok['smwe']:  # token not part of a strong MWE
                tokNum = tok['#']
                sent['swes'][tokNum]['lexlemma'] = tok['lemma']
                assert ' ' not in sent['swes'][tokNum]['lexlemma']
                sent['swes'][tokNum]['toknums'].append(tokNum)

            if tok['wmwe'] and tok['wmwe'][1] == 1:  # first token in weak MWE
                # assert tok['wcat'] and tok['wcat']!='_'    # eventually it would be good to have a category for
                # every weak expression
                sent['wmwes'][tok['wmwe'][0]]['lexcat'] = tok['wcat'] if tok['_lextag'].get('wcat') else None

            if tok['_lextag']['lexcat']:  # first token in a strong expression (SW or MW)
                einfo = tok['_lextag']
                assert einfo['lexcat'] != '_', einfo

                # place to unpack lexcat/supersense info to (lexlemma is already unpacked)
                dest = sent['smwes'][tok['smwe'][0]] if tok['smwe'] else sent['swes'][tok['#']]

                dest['lexcat'] = einfo['lexcat']
                dest['ss'] = ss_mapper(einfo['ss']) if einfo['ss'] != '_' else None
                dest['ss2'] = ss_mapper(einfo['ss2']) if einfo['ss2'] != '_' else None

        for swe in sent['swes'].values():
            assert len(swe['toknums']) == 1, swe
        for smwe in sent['smwes'].values():
            assert smwe['toknums']
        for wmwe in sent['wmwes'].values():
            assert wmwe['toknums']

        for tok in sent['toks']:
            del tok['_lextag']
            if not tok['smwe']:
                assert sent['swes'][tok['#']]['lexcat'], sent['swes']
            else:
                assert sent['smwes'][tok['smwe'][0]]['lexcat'], sent['smwes']

    yield from load_conllulex_sents(inF, morph_syn=morph_syn, misc=misc, ss_mapper=ss_mapper,
                                    unpack=_unpack_lextags, load_columns=load_ud_lextag_columns)


if __name__ == '__main__':
    argparser = ArgumentParser(description=desc)
    add_arguments(argparser)
    print_json(load_sents(**vars(argparser.parse_args())))
