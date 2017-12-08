STREUSLE Dataset
================

STREUSLE stands for Supersense-Tagged Repository of English with a Unified Semantics for Lexical Expressions. It supersedes the Comprehensive __Multiword Expressions__ corpus [1] (which was used for the experiments in [2]). STREUSLE adds semantic supersenses in addition to the MWE annotations. The supersense labels apply to single- and multiword __noun__ and __verb__ expressions, as described in [3], and __preposition__ expressions, as described in [4, 5].

STREUSLE and associated documentation and tools can be downloaded from: <http://www.cs.cmu.edu/~ark/LexSem/>. PrepWiki, the lexical resource that supported preposition supersense annotation and that explains the category hierarchy, can be accessed at <http://tiny.cc/prepwiki>.

This dataset's multiword expression and supersense annotations are licensed under a [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) license (see LICENSE). The source sentences and part-of-speech annotations, which are from the Reviews section of the __English Web Treebank__ (EWTB; [6]), are redistributed with permission of Google and the Linguistic Data Consortium, respectively.

References:

- [1] Nathan Schneider, Spencer Onuffer, Nora Kazour, Emily Danchik, Michael T. Mordowanec, Henrietta Conrad, and Noah A. Smith. Comprehensive annotation of multiword expressions in a social web corpus. _Proceedings of the 9th Linguistic Resources and Evaluation Conference_, Reykjavík, Iceland, May 26–31, 2014. <http://www.cs.cmu.edu/~nschneid/mwecorpus.pdf>

- [2] Nathan Schneider, Emily Danchik, Chris Dyer, and Noah A. Smith. Discriminative lexical semantic segmentation with gaps: running the MWE gamut. _Transactions of the Association for Computational Linguistics_, 2(April):193−206, 2014. http://www.cs.cmu.edu/~ark/LexSem/mwe.pdf

- [3] Nathan Schneider and Noah A. Smith. A corpus and model integrating multiword expressions and supersenses. _Proceedings of the 2015 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies_, Denver, Colorado, May 31–June 5, 2015. <http://www.cs.cmu.edu/~nschneid/sst.pdf>

- [4] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, and Martha Palmer. A hierarchy with, of, and for preposition supersenses. _Proceedings of the 9th Linguistic Annotation Workshop_, Denver, Colorado, June 5, 2015. <http://www.cs.cmu.edu/~nschneid/pssts.pdf>

- [5] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, Meredith Green, Abhijit Suresh, Kathryn Conger, Tim O'Gorman, and Martha Palmer. A corpus of preposition supersenses. _Proceedings of the 10th Linguistic Annotation Workshop_, Berlin, Germany, August 11, 2016. <http://www.cs.cmu.edu/~nschneid/psstcorpus.pdf>

- [6] Ann Bies, Justin Mott, Colin Warner, and Seth Kulick. English Web Treebank. Linguistic Data Consortium, Philadelphia, Pennsylvania, August 16, 2012. <https://catalog.ldc.upenn.edu/LDC2012T13>

Files
-----

- ACKNOWLEDGMENTS.md: Contributors and support that made this dataset possible.
- TAGSET.md: List of class labels with explanations.
- LICENSE: License.
- streusle.sst: Initial annotations, in human-readable and JSON formats, along with gold POS tags.
- streusle.tags: Automatic conversion of streusle.sst to the tagging scheme appropriate for training sequence models. A few intricately structured MWEs have been simplified to fit the tagging scheme, and lemmas from the WordNet lemmatizer have been added.
- streusle.tags.sst: Conversion of streusle.tags back to the .sst format, now with lemmas and tags.
- streusle.upos.tags, streusle.upos.tags.sst: The above files, but replacing gold PTB POS tags with [Universal POS tags](http://universaldependencies.github.io/docs/en/pos/all.html) obtained by applying [this script](https://gist.github.com/nschneid/beed0bcda5b42e530011) to the gold trees in the EWTB.
- STREUSLE3.0-mwes.tsv: All multiword expressions annotated in the corpus: frequency count, lowercased words, strength (`_` = strong MWE, `~` = weak MWE), and part-of-speech sequence.
- STREUSLE3.0-mwe-types.txt: Just the lowercased word sequences annotated as MWEs.
- STREUSLE3.0-strong-mwe-types.txt: Just the strong MWEs.
- psst-tokens.tsv: Human-readable display of preposition supersense annotations, one line per token. (Excludes prepositions labeled with a non-supersense class, such as <code>\`i</code>.)
- Supersense-PB manual verification sample.xlsx: Spreadsheet containing raw data and analysis for the study of correspondences between preposition supersense and PropBank function tags (Schneider et al. 2016, §4). The same spreadsheet can be accessed [online](https://docs.google.com/spreadsheets/d/1DR9z--cPMY2a3y4GghggPe4XNoODO70Da-zPiyMXwg8/edit?usp=sharing) through Google Docs.
- splits/: Experimental train/test splits. See splits/README.md for details.

.sst Format
-----------

(Based on CMWE's .mwe format.) 1 sentence per line. 3 tab-separated columns: sentence ID; human-readable MWE annotation from CMWE; JSON data structure with POS-tagged words, MWE groupings, and class (supersense) annotations associated with the first token of the expression they apply to. Note that token indices are 1-based.

The .tags.sst JSON object adds lemmas and tags in the JSON object.

.tags Format
------------

(CoNLL-esque format based on CMWE's .tags format.) 1 token per line, with blank lines separating sentences.

9 tab-separated columns:

1. token offset
2. word
3. lowercase lemma
4. POS
5. full MWE+class tag
6. offset of parent token (i.e. previous token in the same MWE), if applicable
7. strength level encoded in the tag, if applicable: `_` for strong, `~` for weak
8. class (usually supersense) label, if applicable: see [TAGSET.md](TAGSET.md)
9. sentence ID

Contact
-------

Questions should be directed to:

Nathan Schneider  
[nathan.schneider@georgetown.edu]()  
http://nathan.cl

History
-------

  - STREUSLE 3.0: 2016-08-23. Added preposition supersenses
  - STREUSLE 2.1: 2015-09-25. Various improvements chiefly to auxiliaries, prepositional verbs; added <code>\`p</code> class label as a stand-in for preposition supersenses to be added in a future release, and <code>\`i</code> for infinitival 'to' where it should not receive a supersense. From 2.0 (not counting <code>\`p</code> and <code>\`i</code>):
    * Annotations have changed for 877 sentences (609 involving changes to labels, 474 involving changes to MWEs).
    * 877 class labels have been changed/added/removed, usually involving a non-supersense label or triggered by an MWE change. Most frequently (118 cases) this was to replace `stative` with the auxiliary label <code>\`a</code>. In only 21 cases was a supersense label replaced with a different supersense label.
  - STREUSLE 2.0: 2015-03-29. Added noun and verb supersenses
  - CMWE 1.0: 2014-03-26. Multiword expressions for 55k words of English web reviews
