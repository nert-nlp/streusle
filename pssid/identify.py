import sys
import argparse
import re
import json

from collections import defaultdict
from operator import itemgetter

import tags2sst
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
                    "as well as", "aside from", "at a range of", "at the hand of", "at the hands of",
                    "at the heels of", "bare of", "because of", "by courtesy of",
                    "by dint of", "by force of", "by means of", "by reason of", "by the hand of",
                    "by the hands of", "by the name of", "by virtue of", "by way of", "care of", "complete with",
                    "contrary to", "courtesy of", "depending on", "due to", "except for", "exclusive of",
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
                    "near to", "next to", "nothing short of", "of the name of", "of the order of",
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
                    "within sight of", "nothing but", "just about", "in between",
                    "as long as", "as soon as", "as though", "so long as"} \
#                    .union({"but for", "next door to", "for all", "back of", "as to"})


PREP_SPECIAL_MW_BEGINNERS = ["a", "according", "all", "bare", "because", "but", "care", "complete",
                             "contrary", "courtesy", "depending", "due", "exclusive", "inclusive", "instead",
                             "irrespective", "just", "less", "little", "more", "next", "nothing", "other", "outboard", "owing",
                             "preparatory", "previous", "prior", "pursuant", "rather", "regardless", "relative", "short",
                             "subsequent", "such", "thanks", "this"]



def train(infile, args):
    
    mwe_dict = defaultdict(lambda: defaultdict(int))
    lemma_pos_counts = defaultdict(lambda: defaultdict(int))
    advcl_dict = defaultdict(lambda: defaultdict(int))
    acl_dict = defaultdict(lambda: defaultdict(int))
    swes = defaultdict(int)
    
    for sent in sentences(infile, conllulex=True):
        for token in sent.tokens:
            if token.lexlemma:
                if len(token.lexlemma.split()) > 1:
                    if token.ss and token.ss[0].lower() == "p":
                        mwe_dict["+p"][token.lexlemma] += 1
                    else:
                        mwe_dict["-p"][token.lexlemma] += 1
                elif token.ss and token.ss[0].lower() == "p":
                    swes[token.lemma] += 1
                
            lemma_pos_counts[token.lemma][token.ud_pos] += 1
            lemma_pos_counts[token.lemma][token.ptb_pos] += 1

            if token.ptb_pos == "TO":
                head = sent.tokens[int(token.head)-1]
                matrix = sent.tokens[int(head.head)-1]
                head_has_dir_obj = any(t.head == head.head and t.deprel == "obj" for t in sent.tokens)
                true = token.ss and token.ss[0].lower() == "p"
                
                if head.deprel == "advcl":
                    if true:
                        advcl_dict["+p"][matrix.lemma] += 1
                    else:
                        advcl_dict["-p"][matrix.lemma] += 1
                        
                if head.deprel == "acl":
                    if true:
                        acl_dict["+p"][matrix.lemma] += 1
                    else:
                        acl_dict["-p"][matrix.lemma] += 1

    prep_mwe_list = [k for k, v in sorted(mwe_dict["+p"].items(), key=itemgetter(1), reverse=True) if v >= args.p_mwe_min]
    non_prep_mwe_list = []
    non_prep_mwe_list = [k for k, v in sorted(mwe_dict["-p"].items(), key=itemgetter(1), reverse=True) if v >= args.non_p_mwe_min]
    advcl_list = [k for k, v in sorted(advcl_dict["-p"].items(), key=itemgetter(1), reverse=True) if v >= args.advcl_min]
    acl_list = [k for k, v in sorted(acl_dict["-p"].items(), key=itemgetter(1), reverse=True) if v >= args.acl_min]

    model = {"p_mwe": prep_mwe_list, "non_p_mwe": non_prep_mwe_list, "advcl": advcl_list, "acl": acl_list} # , "lemma_pos": lemma_pos_counts

    outfile = args.model_out if args.model_out else infile.split("/")[-1] + ".p{}-P{}-advcl{}-acl{}.model".format(args.p_mwe_min, args.non_p_mwe_min, args.advcl_min, args.acl_min)
    
    json.dump(model, open(outfile, "w", encoding='utf-8'), indent=2)

    return model




def print_target(token, sentence, index, checkmark, lexcat, context):
    for cont in range(context, 0, -1):
        if index-cont >=0:
            tok = sentence.tokens[index-cont]
            print("-{}\t{}".format(tok.orig, tok.checkmark))
    print((":" if context else "")+"{}\t{}".format(token.orig, checkmark)+("\t{}".format(lexcat) if lexcat else ""))
    for cont in range(1, context+1):
        if index+cont < len(sentence.tokens):
            tok = sentence.tokens[index+cont]
            print("-{}\t{}".format(tok.orig, tok.checkmark))
    if context:
        print()

def heuristicADP(token):
    if token.ud_pos == "ADP" and token.lemma in PREPS_MASTER and token.ptb_pos != "RP":
        return "ADP_*"
    else:
        return ""

def heuristicPossessive(token, sentence):
    if token.ptb_pos in {"PRP$", "WP$"}:
        return "PRON:POSS_*"
    elif token.ptb_pos == "POS":
        head = sentence.tokens[int(token.head)-1]
        return "POS_*"
    return ""

def heuristicSCONJ(token, model):
    if token.ud_pos == "SCONJ" and token.lemma in PREPS_MASTER:
        return "SCONJ_*"
    else:
        return ""

def heuristicADV(token):
    if token.ud_pos == "ADV" and token.ptb_pos == "RB" and token.lemma in PREPS_MASTER:
        return "ADV_*"
    else:
        return ""

def heuristicTO(token, sentence, model):
    if token.ptb_pos == "TO":
        head = sentence.tokens[int(token.head)-1]
        matrix = sentence.tokens[int(head.head)-1]
        head_has_dir_obj = any(t.head == head.head and t.deprel == "obj" for t in sentence.tokens)
        if head.deprel == "advcl":
            if any(t.head == token.head and t.lemma == "for" for t in sentence.tokens):
                return "for_X_TO_*"
            if matrix.ud_pos == "ADJ":
               if any(t.head == matrix.offset and t.lemma == "too" or t.lemma == "enough" for t in sentence.tokens):
                   return "Comparative_TO_*"
            elif matrix.lemma not in model["advcl"]:
                return "not_in_advcl_anti_list_TO_*"
        if head.deprel == "acl" and matrix.lemma not in model["acl"]:
            return "not_in_acl_anti_list_TO_*"
    return ""

def heuristicForXTo(token, sentence):
    if token.head:
        head = sentence.tokens[int(token.head)-1]
        if head.deprel == "advcl" and token.lemma == "for" and \
           any(t.head == token.head and t.ptb_pos == "TO" for t in sentence.tokens[int(token.offset):]):
            return "FOR_X_to"
    return ""

def identify(model, args):

    infile = args.file
    mwe = args.mwe
    evl = args.eval

    mwe_list = set()
    if args.mwe_list:
        with open(args.mwe_list, encoding='utf-8') as f:
            for line in f:
                mwe_list.add(line.strip().split("\t")[0].strip())
    elif "p_mwe" in model:
        mwe_list = set(model["p_mwe"]).union(set(PREPS_MASTER))
    else:
        mwe_list = PREPS_MASTER

    non_prep_mwe_list = set()
    if args.mwe_anti_list:
        with open(args.mwe_anti_list, encoding='utf-8') as f:
            for line in f:
                non_prep_mwe_list.add(line.strip().split("\t")[0].strip())
    elif "non_p_mwe" in model:
        non_prep_mwe_list = model["non_p_mwe"]

    tp, fp, fn, tn = 0, 0, 0, 0
    
    lemma_pos_counts = {}
    for sent in sentences(infile):
        for token in sent.tokens:
            if token.lemma not in lemma_pos_counts:
                lemma_pos_counts[token.lemma] = defaultdict(int)
            lemma_pos_counts[token.lemma][token.ud_pos] += 1
            lemma_pos_counts[token.lemma][token.ptb_pos] += 1
        
    max_mwe_length = max(len(w.split()) for w in mwe_list)
    print("max MWE length={}".format(max_mwe_length), file=sys.stderr)
    mw_beginners = set([w.split()[0] for w in list(mwe_list)+list(non_prep_mwe_list) if len(w.split()) >= 2]).union(set(PREP_SPECIAL_MW_BEGINNERS))

    for si, sent in enumerate(sentences(infile, conllulex=(evl or args.tp or args.fp or args.fn or args.tn)), start=1):
        if not (args.sst or evl or args.tp or args.fp or args.fn or args.tn):
            for metaline in sent.meta:
                print(metaline)

        mwes = []
        mwe_counter = 1
        current_mwe = []

        length = len(sent.tokens)
        i = 0
        k = 0        
        while i < length:
            token = sent.tokens[i]
            lexcat = ""
            if (evl or args.tp or args.fp or args.fn or args.tn):
                try:
                    xlemma = token.fields[12]
                    supersense = token.fields[13]
                except IndexError as e:
                    print("NOTE: the --eval, --tp, --fp, --fn, --tn options works ONLY with full .conllulex format", file=sys.stderr)
                    sys.exit(1)

            t = False
            if (evl or args.tp or args.fp or args.fn or args.tn) and re.match("^p", supersense):
                t = True

            lemma = token.lemma
            skip = False
            if i>=k and (not (evl or args.tp or args.fp or args.fn or args.tn) or supersense != "??"):
                if mwe and token.lemma in mw_beginners:
                    for j in range(min(length, i+max_mwe_length)-1, i+1, -1):
                        ngram = [t for t in sent.tokens[i:j]]
                        ngram_lemma = " ".join([t.lemma for t in ngram])
                        if ngram_lemma in non_prep_mwe_list:
                            skip = True
                            k = j
                            break
                        if ngram_lemma in mwe_list: # find the longest possible mwe
                            mwes.append([int(t.offset) for t in ngram])
                            token.checkmark = "{}:{}".format(mwe_counter, 1) + "**"
                            lemma = ngram_lemma
                            for current_mwe_counter, tok in enumerate(ngram[1:], start=2):
                                sent.tokens[int(tok.offset)-1].checkmark = "{}:{}".format(mwe_counter, current_mwe_counter)
                            if ngram[-1].ud_pos in ("ADP", "SCONJ"):
                                lexcat = "P"
                            else:
                                lexcat = "PP"
                            mwe_counter += 1
                            k = j
                            break

                if not token.checkmark and not skip:
                    token.checkmark += heuristicADP(token) \
                                       + heuristicPossessive(token, sent) \
                                       + heuristicSCONJ(token, model) \
                                       + heuristicADV(token) \
                                       + heuristicTO(token, sent, model) \
                                       + heuristicForXTo(token, sent)
                    
            first_in_mwe = False
            if token.checkmark.endswith("*"):
                if token.checkmark.endswith("**"):
                    first_in_mwe = True
                else:
                    token.checkmark = "*"
                    lexcat = {'PRP$': 'PRON.POSS', 'WP$': 'PRON.POSS', 'POS': 'POSS', 'TO': 'INF.P'}.get(token.ptb_pos, "P")
            elif not (token.checkmark and token.checkmark[0].isdigit()):
                token.checkmark = "-"

            if not args.lexcat:
                lexcat = ""
                
            if token.checkmark == "*" or first_in_mwe:
                if t:
                    # exact match
                    if token.lexlemma == lemma:
                        if args.tp and not evl:
                            print_target(token, sent, i, token.checkmark, lexcat, args.context)
                        tp += 1
                    else:
                        if args.fp and not evl:
                            print_target(token, sent, i, token.checkmark, lexcat, args.context)
                        fp += 1
                        if args.fn and not evl:
                            print_target(token, sent, i, token.checkmark, lexcat, args.context)
                        fn += 1
                else:
                    if args.fp and not evl:
                        print_target(token, sent, i, token.checkmark, lexcat, args.context)
                    fp += 1
            else:
                if t:
                    if args.fn and not evl:
                        print_target(token, sent, i, token.checkmark, lexcat, args.context)
                    fn += 1
                else:
                    if args.tn and not evl:
                        print_target(token, sent, i, token.checkmark, lexcat, args.context)
                    tn += 1

            if not (args.sst or evl or args.tp or args.fp or args.fn or args.tn):
                print("{}\t{}".format(token.orig, token.checkmark) + ("\t{}".format(lexcat) if lexcat else ""))

            i += 1

        if args.sst:
            _json = {}
            _json["words"] = []
            _json["lemmas"] = []
            _json["tags"] = []
            _json["labels"] = {}
            _json["_"] = mwes
            _json["~"] = []
            _sent = []
            for tok in sent.tokens:
                _sent.append(tok.word)
                _json["words"].append([tok.word, tok.ptb_pos])
                _json["lemmas"].append(tok.lemma)
                if tok.checkmark.endswith("*"):
                    _json["labels"][tok.offset] = [tok.word, "Locus"]
            print("{}\t{}\t{}".format(sent.meta_dict.get("sent_id", args.file.split("/")[-1].rsplit(".", maxsplit=1)[0]+"."+str(si)), tags2sst.render(_sent, _json["_"], []).decode("utf-8"), json.dumps(_json)))

        elif not (evl or args.tp or args.fp or args.fn or args.tn):
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

        
def pass_trough_gold(args):
    for sent in sentences(args.file, conllulex=True):
        if not (args.sst or args.eval or args.tp or args.fp or args.fn or args.tn):
            for metaline in sent.meta:
                print(metaline)
        mwes = {}
        for tok in sent.tokens:
            isTarget = tok.ss and tok.ss.startswith("p.")
            isMWE = bool(tok.smwe)
            tok.checkmark = "-"
            if isMWE:
                tok.checkmark = tok.smwe
                if isTarget:
                    tok.checkmark += "**"
                i, j = tok.smwe.split(":")
                if i not in mwes:
                    mwes[i] = []
                mwes[i].append(int(tok.offset))

            elif isTarget:
                tok.checkmark = "*"


            if not (args.sst or args.eval or args.tp or args.fp or args.fn or args.tn):
                print("{}\t{}".format(tok.orig, tok.checkmark) + ("\t{}".format(tok.lexcat) if args.lexcat else ""))

        if args.sst:
            _json = {}
            _json["words"] = []
            _json["lemmas"] = []
            _json["tags"] = []
            _json["labels"] = {}
            _json["_"] = list(mwes.values())
            _json["~"] = []
            _sent = []
            for tok in sent.tokens:
                _sent.append(tok.word)
                _json["words"].append([tok.word, tok.ptb_pos])
                _json["lemmas"].append(tok.lemma)
                if tok.checkmark.endswith("*"):
                    _json["labels"][tok.offset] = [tok.word, tok.ss.split(".")[1]]
            print("{}\t{}\t{}".format(sent.meta_dict["streusle_sent_id"], sent.meta_dict["mwe"], json.dumps(_json)))

        
def main(args):
    if args.gold:
        pass_trough_gold(args)

    else:
        if args.model_file:
            model = json.load(open(args.model_file, encoding='utf-8'))
        elif args.training_file:
            model = train(args.training_file, args)
        else:
            model = train(args.file, args)

        identify(model, args)

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='finds markables heuristically by POS tags and annotates them with an asterisk (*), or two of them (**) for MWEs')
    parser.add_argument('file', type=str, help='path to the .conllulex file')
    parser.add_argument('-f', '--training-file', type=str, help='path to the training .conllulex file')
    parser.add_argument('-M', '--model-file', type=str, help='path to the model file (read)')
    parser.add_argument('-o', '--model-out', type=str, help='path to the model file (write)')
    parser.add_argument('-m', '--mwe', action='store_true', help='also look for mwes')
    parser.add_argument('-l', '--mwe-list', type=str, help='read lexical list of MWEs from file MWE_LIST')
    parser.add_argument('-i', '--mwe-anti-list', type=str, help='read lexical list of MWEs to EXCLUDE from file MWE_ANTI_LIST')
    parser.add_argument('-e', '--eval', action='store_true', help='output evaluation instead of annotated lines; works ONLY with full .conllulex format')
    parser.add_argument('-a', '--tp', action='store_true', help='true positives')
    parser.add_argument('-b', '--fp', action='store_true', help='false positives')
    parser.add_argument('-c', '--fn', action='store_true', help='false negatives')
    parser.add_argument('-d', '--tn', action='store_true', help='true negatives')
    parser.add_argument('-n', '--context', type=int, default=0, help='number of context lines to print before and after target (only has effect when used with --tp, --fp, --fn, or --tn)')
    parser.add_argument('-s', '--sst', action='store_true', help='output .sst format instead of .conlluX format')
    parser.add_argument('-p', '--p-mwe-min', type=int, default=3, help='threshold for prepositional MWE lexicon')
    parser.add_argument('-P', '--non-p-mwe-min', type=int, default=1, help='threshold for non-prepositional MWE lexicon')
    parser.add_argument('--advcl-min', type=int, default=1, help='threshold for advcl heads that take non-prepositional infinitival complements')
    parser.add_argument('--acl-min', type=int, default=1, help='threshold for acl heads that take non-prepositional infinitival complements')
    parser.add_argument('-L', '--lexcat', action='store_true', help='output lexical categories')
    parser.add_argument('-g', '--gold', action='store_true', help='re-use gold standard annotation')
#    parser.add_argument('-v', '--verbose', action='store_true', help='')

    args = parser.parse_args()
    
    main(args)
