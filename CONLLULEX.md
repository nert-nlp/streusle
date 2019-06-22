CoNLL-U-Lex Format
==================

*Nathan Schneider, 2018-01-02*

The file [streusle.conllulex](streusle.conllulex) contains the STREUSLE corpus.
It is structured in a tab-separated format which augments the
10-column [CoNLL-U format](http://universaldependencies.org/format.html)
with 9 additional columns for lexical expressions, for a total of 19 columns.

Sentences are ordered sequentially within documents (reviews);
documents are presented in numerical order by their ID, all in the same file.
Sentences are separated by blank lines.
The markup for each sentence consists of:

- a header section with lines of the form `# key = value`, and
- a body consisting of tokens, one per line.

As an illustration, refer to the following example (preferably in a spreadsheet editor
such as Excel: see [EXCEL.md](EXCEL.md) for instructions).

```
# sent_id = reviews-010378-0002
# text = I did not have a good experience w/ Dr. Ghassemlou.
# streusle_sent_id = ewtb.r.010378.2
# mwe = I did not have_ a good _experience~w / Dr._Ghassemlou .
1	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	4	nsubj	4:nsubj	_	_	PRON	I	_	_	_	_	_	O-PRON
2	did	do	AUX	VBD	Mood=Ind|Tense=Past|VerbForm=Fin	4	aux	4:aux	_	_	AUX	do	_	_	_	_	_	O-AUX
3	not	not	PART	RB	_	4	advmod	4:advmod	_	_	ADV	not	_	_	_	_	_	O-ADV
4	have	have	VERB	VB	VerbForm=Inf	0	root	0:root	_	1:1	V.LVC.full	have experience	v.stative	_	3:1	_	have experience with	B-V.LVC.full-v.stative
5	a	a	DET	DT	Definite=Ind|PronType=Art	7	det	7:det	_	_	DET	a	_	_	_	_	_	o-DET
6	good	good	ADJ	JJ	Degree=Pos	7	amod	7:amod	_	_	ADJ	good	_	_	_	_	_	o-ADJ
7	experience	experience	NOUN	NN	Number=Sing	4	obj	4:obj	_	1:2	_	_	_	_	3:2	_	_	I_
8	w	with	ADP	IN	Abbr=Yes	10	case	10:case	SpaceAfter=No	_	P	with	p.Topic	p.Topic	3:3	_	_	I~-P-p.Topic
9	/	/	PUNCT	,	_	10	punct	10:punct	_	_	PUNCT	/	_	_	_	_	_	O-PUNCT
10	Dr.	Dr.	PROPN	NNP	Number=Sing	7	nmod	7:nmod	_	2:1	N	Dr. Ghassemlou	n.PERSON	_	_	_	_	B-N-n.PERSON
11	Ghassemlou	Ghassemlou	PROPN	NNP	Number=Sing	10	flat	10:flat	SpaceAfter=No	2:2	_	_	_	_	_	_	_	I_
12	.	.	PUNCT	.	_	4	punct	4:punct	_	_	PUNCT	.	_	_	_	_	_	O-PUNCT
```

Header
------

There are 4 pieces of information in the sentence header:

- `sent_id`: the sentence ID in the UD_English corpus
- `text`: the original sentence string
- `streusle_sent_id`: the sentence ID from STREUSLE releases going back to version 1.0;
  this begins with the designator `ewtb.r` for English Web Treebank - Reviews subcorpus.
  The UD_English sentences are the ones from the English Web Treebank, so `sent_id`
  and `streusle_sent_id` are redundant, but including `streusle_sent_id` leaves open
  the possibility of including non-UD sentences in the future.
- `mwe`: a human-readable string consisting of the tokens of the sentence with `_` and `~`
  added to mark up strong and weak MWEs, respectively. Equivalent machine-readable
  information is indicated in the body of the sentence.

Additionally, the first sentence in each document is preceded by a `newdoc` header line.

Body
----

Each token line has the following 19 columns, with `_` indicating an empty value
in a column.

The first 10 columns are copied exactly from the UD_English corpus following the
UDv2 standard. __TODO: The UD_English version is ..., subsequent to 2.0 to incorporate
corrections (primarily to lemmas and POS tags).__
Refer to [this page](http://universaldependencies.org/format.html)
and others on the UD website for documentation of UD's conventions for
encoding orthography, morphology, and syntax.

1. ID: Word index: an integer starting at 1 for each new sentence, or a decimal number for empty nodes that capture ellipsis phenomena. Empty nodes are listed but ignored for purposes of lexical semantics.

2. FORM: Word form or punctuation symbol.

3. LEMMA: Lemma or stem of word form.

4. UPOS: Universal part-of-speech tag, e.g. `ADP` for adpositions.

5. XPOS: Language-specific part-of-speech tag. For UD_English this comes from the Penn Treebank (PTB) tagset: e.g. `IN` for adpositions and subordinating conjunctions.

6. FEATS: List of morphological features, separated by `|` symbols.

7. HEAD: Head of the current word, which is either a value of ID or zero (0).

8. DEPREL: Dependency relation to the HEAD, e.g. `obj` for direct object (`root` iff HEAD = 0).

9. DEPS: Enhanced dependency graph in the form of a list of head-deprel pairs.

10. MISC: Any other annotation. In this corpus, for non-empty (regular) token nodes,
the only thing that goes here is `SpaceAfter=No` to indicate how the tokenization
maps to the original sentence string.

11. SMWE: Two integers, the first identifying a strong MWE grouping of tokens, and the second identifying the current token's position relative to the other tokens that form the MWE. E.g., in the above example, *have* and *experience* form a (discontinuous) strong MWE; *have* has `1:1` in the SMWE column and *experience* has `1:2`. Both integers are 1-based.

12. LEXCAT: A syntactic category that applies to *strong lexical expressions* (strong MWEs and single-word expressions, regardless of whether they belong to a weak MWE).
The set of valid supersense labels (SS and SS2) is determined based on LEXCAT.

    Possible values of LEXCAT are: `N` (noun, common or proper), `PRON` (non-possessive pronoun, including indefinites like *someone*), `PRON.POSS` (possessive pronoun), `POSS` (possessive clitic), `V` (full verb or copula), `AUX` (auxiliary), `P` (single-word adposition), `PP` (prepositional phrase MWE), `INF` (nonsemantic infinitive marker *to* or infinitive-subject-marker *for*), `INF.P` (infinitive maker *to* when it receives an adposition supersense), `DISC` (discourse/pragmatic expression); and `ADJ`, `ADV`, `DET`, `CCONJ`, `SCONJ`, `INTJ`, `NUM`, `SYM`, `PUNCT`, `X`, which are in line with Universal part-of-speech tags. Strong verbal multiword expressions are subtyped, thus receiving a LEXCAT of `V.VID`, `V.VPC.full`, `V.VPC.semi`, `V.LVC.full`, `V.LVC.cause`, or `V.IAV` per [PARSEME Shared Task 1.1 Guidelines](http://parsemefr.lif.univ-mrs.fr/parseme-st-guidelines/1.1/?page=home).

    __Approximately 300 tokens currently have LEXCAT=`!!@` to indicate that they need to be manually corrected, in most cases by adding a noun supersense. These will be fixed in a subsequent release.__

13. LEXLEMMA: The lemma(s) of the component word(s) of the strong expression (single- or multiword) that begins with the current token. `_` for non-initial tokens in a strong MWE. Thus, for *have*, LEXLEMMA is `have experience`, while for `experience` it is `_`.

14. SS: Supersense label, if applicable, and the token is initial within its strong expression. Noun supersense label (prefixed with `n.`; requires LEXCAT=`N`), verb supersense label (prefixed with `v.`; requires LEXCAT=`V`), or adposition supersense label (prefixed with `p.`; requires LEXCAT=`P`, `PP`, `INF.P`, `POSS`, or `PRON.POSS`). Special values are `` `$`` (opaque possessive slot in idiom; requires LEXCAT=`POSS` or `PRON.POSS`) and `??` (unable to assign a supersense because the usage is unintelligible, incomplete, marginal, or nonnative).

15. SS2: Second supersense label; used only for adpositional expressions, which always have two labels listed, a role label in SS and a function label in SS2 (often these are identical).

16. WMWE: Weak MWE grouping and position, analogous to the SMWE column. In the example, *have experience w* forms a weak MWE, and this is indicated with WMWE=`3:1`, `3:2`, and `3:3` on the respective tokens. Weak MWE identifiers are kept distinct from strong MWE identifiers.

17. WLEMMA: If the token begins a weak MWE, as *have* does, then this column holds the lemmas of its constituent words. Otherwise, it is blank (`_`).

18. WCAT: Placeholder for a weak MWE category (currently not used).

19. LEXTAG: BIO-style tag summarizing the full lexical analysis, including any strong and weak MWE segmentations, LEXCAT, and supersenses. This is intended for sequence taggers.

    * The BIO symbols are: `O` for token not belonging to any MWE, `B` for the token beginning an MWE, `I_` for a token continuing a strong MWE, and `I~` for a token continuing a weak MWE. Lowercase variants `o`, `b`, `i_`, and `i~` apply when the token is contained within a separate discontinuous MWE.

    * If the token is not continuing a strong expression (i.e. everything but `I_` and `i_`), the LEXTAG and supersense (if applicable) are appended following hyphens. If SS and SS2 are identical, only one copy is included in the tag; if they differ, they are rendered as SS`|`SS2.

    * Thus, for the tokens *have a good experience w*, the respective LEXTAG values are:

       - *have*: `B-V.LVC.full-v.stative` - begins an MWE, verbal, subtype LVC.full (full light verb construction), stative supersense
       - *a*: `o-DET` - not part of any MWE, but contained within one; determiner, no supersense
       - *good*: `o-ADJ` - not part of any MWE, but contained within one; adjective, no supersense
       - *experience*: `I_` - attaches to the most recent non-`O`/`o` token (*have*) to join it in a strong MWE
       - *w*: `I~-P-p.Topic` - attaches non-`O`/`o` token (*experience*) to join its strong expression (*have experience*) into a weak expression with whatever strong expression contains *w*. Adpositional; SS and SS2 are both `p.Topic`.

Remarks
-------

The CoNLL-U-Lex format was designed to balance machine-readability, human-readability, and interoperability.
It supports workflows such as viewing/editing in a spreadsheet editor, processing by Unix command-line utilities or simple scripts, and viewing a diff of changes in version control.
The replication of CoNLL-U in the first 10 columns gives direct access to rich morphological and syntactic information from the UD project and facilitates easy patching as new versions of the UD data are made available.

To simplify use cases like sorting and filtering by various components of the annotation, there is considerable redundancy in the lexical-level annotations.
The LEXTAG and LEMMA columns are sufficient to reconstruct columns 11-18 and the `mwe` string in the header
(with the exception of 6 sentences, where the analysis in `mwe` is too complex to be encoded below and has
thus been automatically simplified).
The script [UDlextag2json.py](UDlextag2json.py) populates columns 11-18 given columns 1-10 and 19 (LEXTAG).

A script is provided for checking internal consistency of the .conllulex file and converting to a JSON representation: [conllulex2json.py](conllulex2json.py). The JSON format contains the same information but consolidates columns 11-18 into lexical-level data structures under `"swes"` (single-word expressions), `"smwes"` (strong MWEs), and `"wmwes"` (weak MWEs). For Python scripts, the `conllulex2json` module can be imported for loading Python objects directly without storing a JSON file.
[json2conllulex.py](json2conllulex.py) converts in the reverse direction, but does not perform validation.
