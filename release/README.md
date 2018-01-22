STREUSLE Dataset
================

STREUSLE stands for Supersense-Tagged Repository of English with a Unified Semantics for Lexical Expressions. STREUSLE incorporates comprehensive annotations of __multiword expressions__ (MWEs) [1] and semantic supersenses for lexical expressions. The supersense labels apply to single- and multiword __noun__ and __verb__ expressions, as described in [2], and __prepositional__/__possessive__ expressions, as described in [3, 4, 5, 6]. The 4.0 release updates the inventory and application of preposition supersenses [4, 5], applies those supersenses to possessives [6], incorporates the syntactic annotations from the UD project, and adds __lexical category__ labels to indicate the holistic grammatical status of strong multiword expressions.

Release URL: <https://github.com/nert-gu/streusle>  
Additional information: <http://www.cs.cmu.edu/~ark/LexSem/>

This dataset's multiword expression and supersense annotations are licensed under a [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) license (see LICENSE). __TODO: The UD annotations are redistributed under the same license?__ The source sentences and PTB part-of-speech annotations, which are from the Reviews section of the __English Web Treebank__ (EWTB; [7]), are redistributed with permission of Google and the Linguistic Data Consortium, respectively.

An independent effort to improve the MWE annotations from those in STREUSLE 3.0 resulted in the [HAMSTER](https://github.com/eltimster/HAMSTER) resource [10]. The HAMSTER revisions have not been merged with the 4.0 revisions, though we intend to do so for a future release.


Files
-----

- streusle.conllulex: Full dataset.
- STATS.md, LEXCAT.txt, MWES.txt, SUPERSENSES.txt: Statistics summarizing the full dataset.
- train/, dev/, test/: Data splits established by the UD project and accompanying statistics.

- ACKNOWLEDGMENTS.md: Contributors and support that made this dataset possible.
- CONLLULEX.md: Description of data format.
- LICENSE: License.
- papers/: Publications and annotation guidelines.

- conllulex2json.py: Script to validate the data and convert it to JSON.
- lexcatter.py: Utilities for working with lexical categories.
- mwerender.py: Utilities for working with MWEs.
- supersenses.py: Utilities for working with supersense labels.
- tagging.py: Utilities for working with BIO-style tags.
- psseval.py: Evaluation script for preposition/possessive supersense labeling.


Format
------

This release introduces a new tabular data format, [CONLLULEX](CONLLULEX.md), with a script to convert it to JSON. The .sst and .tags formats from STREUSLE 3.0 are not expressive enough for the 4.0 data, and are no longer supported.

References
----------

Citations describing the annotations in this corpus:

- [1] Nathan Schneider, Spencer Onuffer, Nora Kazour, Emily Danchik, Michael T. Mordowanec, Henrietta Conrad, and Noah A. Smith. Comprehensive annotation of multiword expressions in a social web corpus. _Proceedings of the 9th Linguistic Resources and Evaluation Conference_, Reykjavík, Iceland, May 26–31, 2014. <http://people.cs.georgetown.edu/nschneid/p/mwecorpus.pdf>

- [2] Nathan Schneider and Noah A. Smith. A corpus and model integrating multiword expressions and supersenses. _Proceedings of the 2015 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies_, Denver, Colorado, May 31–June 5, 2015. <http://people.cs.georgetown.edu/nschneid/p/sst.pdf>

- [3] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, Meredith Green, Abhijit Suresh, Kathryn Conger, Tim O'Gorman, and Martha Palmer. A corpus of preposition supersenses. _Proceedings of the 10th Linguistic Annotation Workshop_, Berlin, Germany, August 11, 2016. <http://www.cs.cmu.edu/~nschneid/psstcorpus.pdf>

- [4] Jena D. Hwang, Archna Bhatia, Na-Rae Han, Tim O’Gorman, Vivek Srikumar, and Nathan Schneider (2017). Double trouble: the problem of construal in semantic annotation of adpositions. _Proceedings of the Sixth Joint Conference on Lexical and Computational Semantics_, Vancouver, British Columbia, Canada, August 3–4, 2017. <http://people.cs.georgetown.edu/nschneid/p/prepconstrual2.pdf>

- [5] Nathan Schneider, Jena D. Hwang, Archna Bhatia, Na-Rae Han, Vivek Srikumar, Tim O’Gorman, Sarah R. Moeller, Omri Abend, Austin Blodgett, and Jakob Prange (January 16, 2018). Adposition and Case Supersenses v2: Guidelines for English. arXiv preprint. <https://arxiv.org/abs/1704.02134>

- [6] Austin Blodgett and Nathan Schneider (2018). Semantic supersenses for English possessives. _Proceedings of the 11th Linguistic Resources and Evaluation Conference_, Miyazaki, Japan, May 9–11, 2018.


Related work:

- [7] Ann Bies, Justin Mott, Colin Warner, and Seth Kulick. English Web Treebank. Linguistic Data Consortium, Philadelphia, Pennsylvania, August 16, 2012. <https://catalog.ldc.upenn.edu/LDC2012T13>

- [8] Nathan Schneider, Emily Danchik, Chris Dyer, and Noah A. Smith. Discriminative lexical semantic segmentation with gaps: running the MWE gamut. _Transactions of the Association for Computational Linguistics_, 2(April):193−206, 2014. http://www.cs.cmu.edu/~ark/LexSem/mwe.pdf

- [9] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, and Martha Palmer. A hierarchy with, of, and for preposition supersenses. _Proceedings of the 9th Linguistic Annotation Workshop_, Denver, Colorado, June 5, 2015. <http://www.cs.cmu.edu/~nschneid/pssts.pdf>

- [10] King Chan, Julian Brooke, and Timothy Baldwin. Semi-automated resolution of inconsistency for a harmonized multiword expression and dependency parse annotation. _Proceedings of the 13th Workshop on Multiword Expressions_, Valencia, Spain, April 4, 2017. <http://www.aclweb.org/anthology/W/W17/W17-1726.pdf>


Contact
-------

Questions should be directed to:

Nathan Schneider  
[nathan.schneider@georgetown.edu]()  
http://nathan.cl

History
-------

  - STREUSLE 4.0: 2018-01-22. Updated preposition supersenses to new annotation scheme.
    Annotated possessives using preposition supersenses.
    Revised a considerable number of MWEs involving prepositions.
    Added lexical category for every single-word or strong multiword expression.
    New data format (.conllulex) integrates gold syntactic annotations from the
    Universal Dependencies project.
  - STREUSLE 3.0: 2016-08-23. Added preposition supersenses
  - STREUSLE 2.1: 2015-09-25. Various improvements chiefly to auxiliaries, prepositional verbs; added <code>\`p</code> class label as a stand-in for preposition supersenses to be added in a future release, and <code>\`i</code> for infinitival 'to' where it should not receive a supersense. From 2.0 (not counting <code>\`p</code> and <code>\`i</code>):
    * Annotations have changed for 877 sentences (609 involving changes to labels, 474 involving changes to MWEs).
    * 877 class labels have been changed/added/removed, usually involving a non-supersense label or triggered by an MWE change. Most frequently (118 cases) this was to replace `stative` with the auxiliary label <code>\`a</code>. In only 21 cases was a supersense label replaced with a different supersense label.
  - STREUSLE 2.0: 2015-03-29. Added noun and verb supersenses
  - CMWE 1.0: 2014-03-26. Multiword expressions for 55k words of English web reviews
