Canonical format: CoNLL-U
=========================

The [.conllu Format](https://universaldependencies.org/format.html) is the official 
format of the Universal Dependencies (UD) project. STREUSLE adheres to that format,
encoding lexical semantic information via attributes in the MISC column. These annotations
can therefore be included in the official release of the
[UD_English-EWT corpus](https://universaldependencies.org/treebanks/en_ewt/index.html).

(In the 4.x releases of STREUSLE, the canonical format was .conllulex,
which has been [deprecated](/deprecated/).)

The STREUSLE attributes (key-value pairs) are given below.

MWE attributes
--------------

  - `MWECat` (lexical category of the MWE)
      UPOS values: `ADJ`, `ADV`, `AUX`, `CCONJ`, `DET`, `INTJ`, `NUM`, `PRON`,
        `SCONJ`, `SYM`
      Other values: `DISC` (discourse), `INF.P` (SNACS-labeled infinitival idiom),
        `N` (common or proper multiword noun expression), `P` (multiword preposition),
        `PP` (idiomatic prepositional phrase), and the verbal MWE subtypes:
        `V.IAV`, `V.LVC.cause`, `V.LVC.full`, `V.VID`, `V.VPC.full`, `V.VPC.semi`
  - `MWELemma` (sequence of word lemmas and gap-lengths, e.g. "go out of <1> way"
      for "went out of their way")
  - `MWEString` (surface forms if different from `MWELemma` beyond capitalization).
      N.B. `goeswith` tokens are separated by spaces in `MWEString` but not `MWELemma`.
  - `MWELen` (length of span from first to last token of the MWE)

The attributes are placed on the first word of the MWE.
Plain `MWECat`, `MWELemma`, `MWELen` togther represent a strong expression.
A weak expression is represented with `MWECat[weak]`, `MWELemma[weak]`, `MWELen[weak]`.

Supersense attributes
---------------------

  - `Supersense` (if there is only one, i.e. all nouns/verbs and many prepositions),
      *OR* `Supersense[coding]` (a.k.a. function or `ss2`) and `Supersense[scene]` (a.k.a. role or `ss`).
      Noun and verb supersenses start with `n.` and `v.` respectively.
      SNACS supersenses start with `p.`, except for the special labels `` `$ ``
      (possessive slot in idiom) and `??` (ungrammatical/unintelligible).
      Other special labels are `` `d `` (single-word discourse expression tagged as a noun,
      verb, or preposition/possessive), `` `j `` (single-word adjectival expression
      tagged as a verb), and `` `c `` (coordinator tagged as an ADP).
  - `PRel[config]`, `PRel[gov]`, `PRel[obj]` (structure of the prepositional/possessive 
      relation associated with a SNACS supersense; some constructions lack a governor
      [approximator or PP idiom] or an object [intransitive P])

An example
----------

```conllu
# sent_id = reviews-010378-0002
# newpar id = reviews-010378-p0002
# text = I did not have a good experience w/ Dr. Ghassemlou.
# streusle_sent_id = ewtb.r.010378.2
# mwe = I did not have_ a good _experience~w / Dr._Ghassemlou .
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	4	nsubj	4:nsubj	_
2	did	do	AUX	VBD	Mood=Ind|Number=Sing|Person=1|Tense=Past|VerbForm=Fin	4	aux	4:aux	_
3	not	not	PART	RB	Polarity=Neg	4	advmod	4:advmod	_
4	have	have	VERB	VB	VerbForm=Inf	0	root	0:root	MWECat=V.LVC.full|MWELemma=have <2> experience|MWELemma[weak]=have <2> experience with|MWELen=4|MWELen[weak]=5|MWEString[weak]=have <2> experience w|Supersense=v.stative
5	a	a	DET	DT	Definite=Ind|PronType=Art	7	det	7:det	_
6	good	good	ADJ	JJ	Degree=Pos	7	amod	7:amod	_
7	experience	experience	NOUN	NN	Number=Sing	4	obj	4:obj	_
8	w	with	ADP	IN	Abbr=Yes	11	case	11:case	SpaceAfter=No|PRel[config]=default|PRel[gov]=7:experience|PRel[obj]=11:Ghassemlou|Supersense=p.Topic
9	/	/	PUNCT	,	_	8	punct	8:punct	_
10	Dr.	Dr.	PROPN	NNP	Number=Sing	11	nmod:desc	11:nmod:desc	MWECat=N|MWELemma=Dr. Ghassemlou|MWELen=2|Supersense=n.PERSON
11	Ghassemlou	Ghassemlou	PROPN	NNP	Number=Sing	7	nmod	7:nmod:with	SpaceAfter=No
12	.	.	PUNCT	.	_	4	punct	4:punct	_
```

JSON Format
===========

conllu2json.py produces a simpler machine-readable encoding of the data.
JSON files are included in the release for the [train](train/streusle.ud_train.json),
[dev](dev/streusle.ud_dev.json), and [test](dev/streusle.ud_test.json) portions of the data.

Each sentence is an object with the following keys:

| Key | Explanation |
----------|-------------------------------------------------
`sent_id` | UD sentence ID
`text`    | surface sentence string
`streusle_sent_id` | old-style STREUSLE ID
`mwe`     | textual rendering of multiword expression markup
`toks`    | word tokens in the basic UD graph
`etoks`   | word tokens in the enhanced UD graph only
`swes`    | single-word lexical expressions
`smwes`   | strong multiword expressions
`wmwes`   | weak multiword expressions


MWE group offsets
-----------------

The strong and weak MWEs are sorted by the token position of the first word
(ties broken as strong before weak) and numbered starting from 1. These expression group
numbers are computed automatically; they do not appear in the .conllu file.

Lexcat and lextag
-----------------

These pieces of information are not (fully) explicit in the .conllu, but are generated
in the JSON format:

- The __lexcat__ is the syntax-based category to which the strong lexical expression
  (single- or multi-word) belongs. In .conllu it is explicit only for MWEs, as the `MWECat`.
  For single-word expressions, it is inferred based on the UPOS when converting to JSON.
  Exceptions in the UPOS-to-lexcat mapping are indicated with special labels in the
  `Supersense` field. The relationship between lexcats and allowed supersenses is specified in
  [lexcatter.py](lexcatter.py).
- Each word token has a __lextag__ such that the lexical semantic annotations can be recovered
  from the full sequence of these tags. This can be useful for training tagger models.
  Examples include `O-ADV`, `B-V.LVC.full-v.stative`, `I_`. Lextags are generated in the JSON
  (see below).

For details on interpreting these fields see [CONLLULEX.md](deprecated/CONLLULEX.md).

An example
----------

```json
{
 "sent_id": "reviews-010378-0002",
 "extra_meta": [
  "# newpar id = reviews-010378-p0002"
 ],
 "text": "I did not have a good experience w/ Dr. Ghassemlou.",
 "streusle_sent_id": "ewtb.r.010378.2",
 "mwe": "I did not have_ a good _experience~w / Dr._Ghassemlou .",
    "toks": [
      {"#": 1, "word": "I", "lemma": "I", "upos": "PRON", "xpos": "PRP", "feats": "Case=Nom|Number=Sing|Person=1|PronType=Prs", "head": 4, "deprel": "nsubj", "edeps": "4:nsubj", "misc": null, "smwe": null, "wmwe": null, "lextag": "O-PRON"},
      {"#": 2, "word": "did", "lemma": "do", "upos": "AUX", "xpos": "VBD", "feats": "Mood=Ind|Number=Sing|Person=1|Tense=Past|VerbForm=Fin", "head": 4, "deprel": "aux", "edeps": "4:aux", "misc": null, "smwe": null, "wmwe": null, "lextag": "O-AUX"},
      {"#": 3, "word": "not", "lemma": "not", "upos": "PART", "xpos": "RB", "feats": "Polarity=Neg", "head": 4, "deprel": "advmod", "edeps": "4:advmod", "misc": null, "smwe": null, "wmwe": null, "lextag": "O-ADV"},
      {"#": 4, "word": "have", "lemma": "have", "upos": "VERB", "xpos": "VB", "feats": "VerbForm=Inf", "head": 0, "deprel": "root", "edeps": "0:root", "misc": ["MWECat=V.LVC.full", "MWELemma=have <2> experience", "MWELemma[weak]=have <2> experience with", "MWELen=4", "MWELen[weak]=5", "MWEString[weak]=have <2> experience w", "Supersense=v.stative"], "smwe": [1, 1], "wmwe": [2, 1], "lextag": "B-V.LVC.full-v.stative"},
      {"#": 5, "word": "a", "lemma": "a", "upos": "DET", "xpos": "DT", "feats": "Definite=Ind|PronType=Art", "head": 7, "deprel": "det", "edeps": "7:det", "misc": null, "smwe": null, "wmwe": null, "lextag": "o-DET"},
      {"#": 6, "word": "good", "lemma": "good", "upos": "ADJ", "xpos": "JJ", "feats": "Degree=Pos", "head": 7, "deprel": "amod", "edeps": "7:amod", "misc": null, "smwe": null, "wmwe": null, "lextag": "o-ADJ"},
      {"#": 7, "word": "experience", "lemma": "experience", "upos": "NOUN", "xpos": "NN", "feats": "Number=Sing", "head": 4, "deprel": "obj", "edeps": "4:obj", "misc": null, "smwe": [1, 2], "wmwe": [2, 2], "lextag": "I_"},
      {"#": 8, "word": "w", "lemma": "with", "upos": "ADP", "xpos": "IN", "feats": "Abbr=Yes", "head": 11, "deprel": "case", "edeps": "11:case", "misc": ["PRel[config]=default", "PRel[gov]=7:experience", "PRel[obj]=11:Ghassemlou", "SpaceAfter=No", "Supersense=p.Topic"], "heuristic_relation": {"gov": 7, "govlemma": "experience", "obj": 11, "objlemma": "Ghassemlou", "config": "default"}, "smwe": null, "wmwe": [2, 3], "lextag": "I~-P-p.Topic"},
      {"#": 9, "word": "/", "lemma": "/", "upos": "PUNCT", "xpos": ",", "feats": null, "head": 8, "deprel": "punct", "edeps": "8:punct", "misc": null, "smwe": null, "wmwe": null, "lextag": "O-PUNCT"},
      {"#": 10, "word": "Dr.", "lemma": "Dr.", "upos": "PROPN", "xpos": "NNP", "feats": "Number=Sing", "head": 11, "deprel": "nmod:desc", "edeps": "11:nmod:desc", "misc": ["MWECat=N", "MWELemma=Dr. Ghassemlou", "MWELen=2", "Supersense=n.PERSON"], "smwe": [3, 1], "wmwe": null, "lextag": "B-N-n.PERSON"},
      {"#": 11, "word": "Ghassemlou", "lemma": "Ghassemlou", "upos": "PROPN", "xpos": "NNP", "feats": "Number=Sing", "head": 7, "deprel": "nmod", "edeps": "7:nmod:with", "misc": ["SpaceAfter=No"], "smwe": [3, 2], "wmwe": null, "lextag": "I_"},
      {"#": 12, "word": ".", "lemma": ".", "upos": "PUNCT", "xpos": ".", "feats": null, "head": 4, "deprel": "punct", "edeps": "4:punct", "misc": null, "smwe": null, "wmwe": null, "lextag": "O-PUNCT"}
    ],
    "etoks": [],
    "swes": {
      "1": {"lexlemma": "I", "lexcat": "PRON", "ss": null, "ss2": null, "toknums": [1]},
      "2": {"lexlemma": "do", "lexcat": "AUX", "ss": null, "ss2": null, "toknums": [2]},
      "3": {"lexlemma": "not", "lexcat": "ADV", "ss": null, "ss2": null, "toknums": [3]},
      "5": {"lexlemma": "a", "lexcat": "DET", "ss": null, "ss2": null, "toknums": [5]},
      "6": {"lexlemma": "good", "lexcat": "ADJ", "ss": null, "ss2": null, "toknums": [6]},
      "8": {"lexlemma": "with", "lexcat": "P", "ss": "p.Topic", "ss2": "p.Topic", "toknums": [8]},
      "9": {"lexlemma": "/", "lexcat": "PUNCT", "ss": null, "ss2": null, "toknums": [9]},
      "12": {"lexlemma": ".", "lexcat": "PUNCT", "ss": null, "ss2": null, "toknums": [12]}
    },
    "smwes": {
      "1": {"lexlemma": "have experience", "lexcat": "V.LVC.full", "ss": "v.stative", "ss2": null, "toknums": [4, 7]},
      "3": {"lexlemma": "Dr. Ghassemlou", "lexcat": "N", "ss": "n.PERSON", "ss2": null, "toknums": [10, 11]}
    },
    "wmwes": {
      "2": {"lexlemma": "have experience with", "toknums": [4, 7, 8], "lexcat": null}
    }
}
```
