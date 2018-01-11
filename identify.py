import sys
import argparse
import re

from collections import defaultdict


from helpers import *

PREPS_MASTER = {"a", "abaft", "aboard", "about", "above", "abreast", "abroad", "absent", "across",
                    "adrift", "afore", "aft", "after", "afterward", "afterwards", "against", "agin", "ago",
                    "aground", "ahead", "aloft", "along", "alongside", "amid", "amidst", "among", "amongst",
                    "an", "anent", "anti", "apart", "apropos", "apud", "around", "as", "ashore", "aside",
                    "aslant", "astraddle", "astride", "asunder", "at", "athwart", "atop", "away", "back",
                    "backward", "backwards", "bar", "barring", "before", "beforehand", "behind", "below",
                    "beneath", "beside", "besides", "between", "betwixt", "beyond", "but", "by", "c.", "cept",
                    "chez", "circa", "come", "concerning", "considering", "counting", "cum", "dehors", "despite",
                    "down", "downhill", "downstage", "downstairs", "downstream", "downward", "downwards",
                    "downwind", "during", "eastward", "eastwards", "ere", "ex", "except", "excepting", "excluding",
                    "failing", "following", "for", "forbye", "fore", "fornent", "forth", "forward", "forwards",
                    "frae", "from", "gainst", "given", "gone", "granted", "heavenward", "heavenwards", "hence",
                    "henceforth", "home", "homeward", "homewards", "in", "including", "indoors", "inside", "into",
                    "inward", "inwards", "leftward", "leftwards", "less", "like", "mid", "midst", "minus",
                    "mod", "modulo", "mongst", "near", "nearby", "neath", "next", "nigh", "northward", "northwards",
                    "notwithstanding", "o'", "o'er", "of", "off", "on", "onto", "onward", "onwards", "opposite",
                    "out", "outdoors", "outside", "outta", "outward", "outwards", "outwith", "over", "overboard",
                    "overhead", "overland", "overseas", "overtop", "pace", "past", "pending", "per", "plus", "pon",
                    "post", "pro", "qua", "re", "regarding", "respecting", "rightward", "rightwards", "round",
                    "sans", "save", "saving", "seaward", "seawards", "since", "skyward", "skywards", "southward",
                    "southwards", "than", "thenceforth", "thro'", "through", "throughout", "thru", "thruout",
                    "thwart", "'til", "till", "times", "to", "together", "touching", "toward", "towards", "under",
                    "underfoot", "underground", "underneath", "unlike", "until", "unto", "up", "uphill", "upon",
                    "upside", "upstage", "upstairs", "upstream", "upward", "upwards", "upwind", "v.", "versus",
                    "via", "vice", "vis-a-vis", "vis-à-vis", "vs.", "w/", "w/i", "w/in", "w/o", "westward",
                    "westwards", "with", "withal", "within", "without",
                    "a cut above", "a la", "à la", "according to", "after the fashion of", "ahead of", "all for",
                    "all over", "along with", "apart from", "as far as", "as for", "as from", "as of",
                    "as opposed to", "as regards",
                    "as to", "as well as", "aside from", "at a range of", "at the hand of", "at the hands of",
                    "at the heels of", "back of", "bare of", "because of", "but for", "by courtesy of",
                    "by dint of", "by force of", "by means of", "by reason of", "by the hand of",
                    "by the hands of", "by the name of", "by virtue of", "by way of", "care of", "complete with",
                    "contrary to", "courtesy of", "depending on", "due to", "except for", "exclusive of", "for all",
                    "for the benefit of", "give or take", "having regard to", "in accord with", "in addition to",
                    "in advance of", "in aid of", "in back of", "in bed with", "in behalf of", "in case of",
                    "in common with", "in company with", "in connection with", "in consideration of",
                    "in contravention of", "in default of", "in excess of", "in face of", "in favor of",
                    "in favour of", "in front of", "in honor of", "in honour of", "in keeping with", "in lieu of",
                    "in light of", "in line with", "in memoriam", "in need of", "in peril of", "in place of",
                    "in proportion to", "in re", "in reference to", "in regard to", "in relation to",
                    "in respect of", "in sight of", "in spite of", "in terms of", "in the course of",
                    "in the face of", "in the fashion of", "in the grip of", "in the light of", "in the matter of",
                    "in the midst of", "in the name of", "in the pay of", "in the person of", "in the shape of",
                    "in the teeth of", "in the throes of", "in token of", "in view of", "in virtue of",
                    "inclusive of", "inside of", "instead of", "irrespective of", "little short of", "more like",
                    "near to", "next door to", "next to", "nothing short of", "of the name of", "of the order of",
                    "on a level with", "on a par with", "on account of", "on behalf of", "on pain of",
                    "on the order of", "on the part of", "on the point of", "on the score of", "on the strength of",
                    "on the stroke of", "on top of", "other than", "out of", "out of keeping with",
                    "out of line with", "outboard of", "outside of", "over against", "over and above", "owing to",
                    "preparatory to", "previous to", "prior to", "pursuant to", "regardless of", "relative to",
                    "round about", "short for", "short of", "such as", "subsequent to", "thanks to", "this side of",
                    "to the accompaniment of", "to the tune of", "together with", "under cover of", "under pain of",
                    "under sentence of", "under the heel of", "up against", "up and down", "up before", "up for",
                    "up to", "upward of", "upwards of", "vis a vis", "vis à vis", "vis - a - vis", "vis - à - vis",
                    "with reference to", "with regard to", "with respect to", "with the exception of",
                    "within sight of",
                    "rather then", "nothing but", "just about", "in between",
                    "as long as", "as soon as", "as though", "so long as"}


PREP_SPECIAL_MW_BEGINNERS = ["a", "according", "all", "bare", "because", "but", "care", "complete",
                             "contrary", "courtesy", "depending", "due", "exclusive", "inclusive", "instead",
                             "irrespective", "just", "less", "little", "more", "next", "nothing", "other", "outboard", "owing",
                             "preparatory", "previous", "prior", "pursuant", "rather", "regardless", "relative", "short",
                             "subsequent", "such", "thanks", "this"]





TAGS_PTB = ["IN", "RB", "RP", "PRP$", "WP$", "POS", "TO"]
TAGS_UD = ["ADP", "SCONJ", "ADV", "PRON", "PART"]


def print_target(token, sentence, index, checkmark, context):
    for cont in range(context, 0, -1):
        if index-cont >=0:
            print("-{}".format(sentence.tokens[index-cont].orig))
    print((":" if context else "")+"{}\t{}".format(token.orig, checkmark))
    for cont in range(1, context+1):
        if index+cont < len(sentence.tokens):
            print("-{}".format(sentence.tokens[index+cont].orig))
    if context:
        print()


def main(args):

    infile = args.file
    tagset = args.tagset
    mwe = args.mwe
    evl = args.eval

    mwe_list = set()
    if args.mwe_list:
        with open(args.mwe_list) as f:
            for line in f:
                mwe_list.add(line.strip().split("\t")[0].strip())
    else:
        mwe_list = PREPS_MASTER        

    tp, fp, fn, tn = 0, 0, 0, 0
    
    lemma_pos_counts = {}
    for sent in sentences(infile):
        for token in sent.tokens:
            if token.lemma not in lemma_pos_counts:
                lemma_pos_counts[token.lemma] = defaultdict(int)
            lemma_pos_counts[token.lemma][token.ud_pos] += 1
            lemma_pos_counts[token.lemma][token.ptb_pos] += 1
        
    max_mwe_length = max(len(w.split()) for w in mwe_list)
    mw_beginners = set([w.split()[0] for w in mwe_list if len(w.split()) >= 2]).union(set(PREP_SPECIAL_MW_BEGINNERS))

    for sent in sentences(infile):
        if not (evl or args.tp or args.fp or args.fn or args.tn):
            for metaline in sent.meta:
                print(metaline)

        length = len(sent.tokens)
        i = 0
        k = 0
        while i < length:
            token = sent.tokens[i]
            if (evl or args.tp or args.fp or args.fn or args.tn):
                try:
                    xlemma = token.fields[12]
                    lexcat = token.fields[13]
                except IndexError as e:
                    print("NOTE: the --eval, --tp, --fp, --fn, --tn options works ONLY with full .conllulex format", file=sys.stderr)
                    sys.exit(1)

            t = False
            if (evl or args.tp or args.fp or args.fn or args.tn) and re.match("^(p|\?)", lexcat):
                t = True

            lemma = token.lemma
            checkmark = ""
            if i>=k:
                if mwe and token.lemma in mw_beginners: # find the longest possible mwe
                    for j in range(min(length, i+max_mwe_length)-1, i+1, -1):
                        ngram = [t for t in sent.tokens[i:j]]
                        ngram_lemma = " ".join([t.lemma for t in ngram])
                        if ngram_lemma in mwe_list:
                            lemma = ngram_lemma
                            checkmark = lemma + "_**"
                            k = j
                            break

                if not checkmark:
                    if token.ud_pos == "ADP" and token.ptb_pos != "RP" and token.lemma in PREPS_MASTER:
                        checkmark = "ADP_*"
                    elif token.ptb_pos in {"PRP$", "WP$", "POS"}:
                        checkmark = "PRP$_WP$_POS_*"
                    elif token.ud_pos == "SCONJ" and token.lemma in PREPS_MASTER: # and lemma_pos_counts[token.lemma]["ADP"] >= 20:
                        checkmark = "SCONJ_*"
                    elif token.ud_pos == "ADV" and token.ptb_pos == "RB" and token.lemma in PREPS_MASTER:
                        checkmark = "ADV_RB_*"
                    elif token.ptb_pos == "TO":
                        head = sent.tokens[int(token.head)-1]
                        matrix = sent.tokens[int(head.head)-1]
                        head_has_dir_obj = any(t.head == head.head and t.deprel == "obj" for t in sent.tokens)
                        if head.deprel in {"advcl"}:
                            checkmark = "TO_*"
            if checkmark:
                if t:
                    if args.tp and not evl:
                        print_target(token, sent, i, checkmark, args.context)
                    tp += 1
                else:
                    if args.fp and not evl:
                        print_target(token, sent, i, checkmark, args.context)
                    fp += 1
            else:
                if t:
                    if args.fn and not evl:
                        print_target(token, sent, i, checkmark, args.context)
                    fn += 1
                else:
                    if args.tn and not evl:
                        print_target(token, sent, i, checkmark, args.context)
                    tn += 1
            if not (evl or args.tp or args.fp or args.fn or args.tn):
                print("{}\t{}".format(token.orig, checkmark))

            i += 1
        if not (evl or args.tp or args.fp or args.fn or args.tn):
            print()

    if evl:
        print("\tgold+\tgold-")
        print("auto+\t{}\t{}\t{}".format(tp, fp, tp+fp))
        print("auto-\t{}\t{}\t{}".format(fn, tn, fn+tn))
        print("\t{}\t{}\t{}".format(tp+fn, fp+tn, tp+fp+tn+fn))
        p = tp/(tp+fp)
        r = tp/(tp+fn)
        f = (2*p*r)/(p+r)
        print("\nP\tR\tF")
        print("{}\t{}\t{}".format(p, r, f))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='finds markables heuristically by POS tags and annotates them with an asterisk (*), or two of them (**) for MWEs')
    parser.add_argument('file', type=str, help='path to the .conllulex file')
    parser.add_argument('-t', '--tagset', type=str, help='one of {UD, PTB}', default="PTB")
    parser.add_argument('-m', '--mwe', action='store_true', help='also look for mwes')
    parser.add_argument('-l', '--mwe-list', type=str, help='read lexical list of MWEs from file MWE_LIST')
    parser.add_argument('-e', '--eval', action='store_true', help='output evaluation instead of annotated lines; works ONLY with full .conllulex format')
    parser.add_argument('-a', '--tp', action='store_true', help='true positives')
    parser.add_argument('-b', '--fp', action='store_true', help='false positives')
    parser.add_argument('-c', '--fn', action='store_true', help='false negatives')
    parser.add_argument('-d', '--tn', action='store_true', help='true negatives')
    parser.add_argument('-n', '--context', type=int, default=0, help='number of context lines to print before and after target (only has effect when used with --tp, --fp, --fn, or --tn)')
    
#    parser.add_argument('-v', '--verbose', action='store_true', help='')

    args = parser.parse_args()
    
    main(args)
