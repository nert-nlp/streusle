STREUSLE Dataset
================

| ![Example](example.png)  |
|:---:|
| *STREUSLE annotations visualized with streusvis.py* |

STREUSLE stands for Supersense-Tagged Repository of English with a Unified Semantics for Lexical Expressions. The text is from the web reviews portion of the English Web Treebank [8]. STREUSLE incorporates comprehensive annotations of __multiword expressions__ (MWEs) [1] and semantic supersenses for lexical expressions. The supersense labels apply to single- and multiword __noun__ and __verb__ expressions, as described in [2], and __prepositional__/__possessive__ expressions, as described in [3, 4, 5, 6, 7]. The 4.0 release [7] updates the inventory and application of preposition supersenses, applies those supersenses to possessives (detailed in [6]), incorporates the syntactic annotations from the Universal Dependencies project, and adds __lexical category__ labels to indicate the holistic grammatical status of strong multiword expressions. The 4.1 release adds subtypes for verbal MWEs (VID, VPC.{full,semi}, LVC.{full,cause}, IAV) according to PARSEME 1.1 guidelines [14].

Release URL: <https://github.com/nert-nlp/streusle>  
Additional information: <http://www.cs.cmu.edu/~ark/LexSem/>

The English Web Treebank sentences were also used by the [Universal Dependencies](http://universaldependencies.org/) (UD) project as the primary reference corpus for English [9]. STREUSLE incorporates the syntactic and morphological parses from UD\_English-EWT v2.2 (with the exception of one lemma, token 14 in reviews-091704-0004, which is a typo); these were released July 1, 2018 and follow the UD v2 standard.

This dataset's multiword expression and supersense annotations are licensed under a [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/) license (see LICENSE). The UD annotations are redistributed under the same license. The source sentences and PTB part-of-speech annotations, which are from the Reviews section of the __English Web Treebank__ (EWTB; [8]), are redistributed with permission of Google and the Linguistic Data Consortium, respectively.

An independent effort to improve the MWE annotations from those in STREUSLE 3.0 resulted in the [HAMSTER](https://github.com/eltimster/HAMSTER) resource [13]. The HAMSTER revisions have not been merged with the 4.0 revisions, though we intend to do so for a future release.


Files
-----

- streusle.conllulex: Full dataset.
- STATS.md, LEXCAT.txt, MWES.txt, SUPERSENSES.txt: Statistics summarizing the full dataset.
- train/, dev/, test/: Data splits established by the UD project and accompanying statistics.
- releaseutil/: Scripts for preparing the data for release.

- ACKNOWLEDGMENTS.md: Contributors and support that made this dataset possible.
- CONLLULEX.md: Description of data format.
- EXCEL.md: Instructions for working with the data as a spreadsheet.
- LICENSE.txt: License.
- ACL2018.md: Links to resources reported in [7].

- conllulex2json.py: Script to validate the data and convert it to JSON.
- json2conllulex.py: Script to convert STREUSLE JSON to .conllulex.
- conllulex2csv.py: Script to create an Excel-readable CSV file with the data.
- csv2conllulex.py: Script to convert an Excel-generated CSV file to .conllulex.
- conllulex2UDlextag.py: Script to remove all STREUSLE fields except lextags.
- UDlextag2json.py: Script to unpack lextags, populating remaining STREUSLE fields.
- normalize_mwe_numbering.py: Script to ensure MWEs within each sentence are numbered in a consistent order.

- govobj.py: Utility for adding heuristic preposition/possessor governor and object links to the JSON.
- lexcatter.py: Utilities for working with lexical categories.
- mwerender.py: Utilities for working with MWEs.
- supersenses.py: Utilities for working with supersense labels.
- streusvis.py: Utility for browsing MWE and supersense annotations.
- supdate.py: Utility for applying lexical semantic annotations made by editing the output of streusvis.py.
- tagging.py: Utilities for working with BIO-style tags.
- tquery.py: Utility for searching the data for tokens that meet certain criteria.
- tupdate.py: Utility for applying lexical tag changes made by editing the output of tquery.py.
- streuseval.py: Unified evaluation script for MWEs and supersenses.
- psseval.py: Evaluation script for preposition/possessive supersense labeling only.
- pssid/: Heuristics for identifying SNACS targets.

Format
------

STREUSLE 4.0+ uses the [CONLLULEX](CONLLULEX.md) tabular data format, with scripts to convert to and from JSON as well as [Excel-compatible CSV](EXCEL.md). (The .sst and .tags formats from STREUSLE 3.0 are not expressive enough and are no longer supported.)

References
----------

Citations describing the annotations in this corpus (main STREUSLE papers in __bold__):

- [1] Nathan Schneider, Spencer Onuffer, Nora Kazour, Emily Danchik, Michael T. Mordowanec, Henrietta Conrad, and Noah A. Smith. Comprehensive annotation of multiword expressions in a social web corpus. _Proceedings of the Ninth International Conference on Language Resources and Evaluation_, Reykjavík, Iceland, May 26–31, 2014. <http://people.cs.georgetown.edu/nschneid/p/mwecorpus.pdf>

- __[2] Nathan Schneider and Noah A. Smith. A corpus and model integrating multiword expressions and supersenses. _Proceedings of the 2015 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies_, Denver, Colorado, May 31–June 5, 2015. <http://people.cs.georgetown.edu/nschneid/p/sst.pdf>__

- [3] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, Meredith Green, Abhijit Suresh, Kathryn Conger, Tim O'Gorman, and Martha Palmer. A corpus of preposition supersenses. _Proceedings of the 10th Linguistic Annotation Workshop_, Berlin, Germany, August 11, 2016. <http://people.cs.georgetown.edu/nschneid/p/psstcorpus.pdf>

- [4] Jena D. Hwang, Archna Bhatia, Na-Rae Han, Tim O’Gorman, Vivek Srikumar, and Nathan Schneider. Double trouble: the problem of construal in semantic annotation of adpositions. _Proceedings of the Sixth Joint Conference on Lexical and Computational Semantics_, Vancouver, British Columbia, Canada, August 3–4, 2017. <http://people.cs.georgetown.edu/nschneid/p/prepconstrual2.pdf>

- [5] Nathan Schneider, Jena D. Hwang, Archna Bhatia, Na-Rae Han, Vivek Srikumar, Tim O’Gorman, Sarah R. Moeller, Omri Abend, Austin Blodgett, and Jakob Prange (July 2, 2018). Adposition and Case Supersenses v2: Guidelines for English. arXiv preprint. <https://arxiv.org/abs/1704.02134>

- [6] Austin Blodgett and Nathan Schneider (2018). Semantic supersenses for English possessives. _Proceedings of the 11th International Conference on Language Resources and Evaluation_, Miyazaki, Japan, May 9–11, 2018. <http://people.cs.georgetown.edu/nschneid/p/gensuper.pdf>

- __[7] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, Jakob Prange, Austin Blodgett, Sarah R. Moeller, Aviram Stern, Adi Bitan, and Omri Abend. Comprehensive supersense disambiguation of English prepositions and possessives. _Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics_, Melbourne, Australia, July 15–20, 2018. <http://people.cs.georgetown.edu/nschneid/p/pssdisambig.pdf>__

Related work:

- [8] Ann Bies, Justin Mott, Colin Warner, and Seth Kulick. English Web Treebank. Linguistic Data Consortium, Philadelphia, Pennsylvania, August 16, 2012. <https://catalog.ldc.upenn.edu/LDC2012T13>

- [9] Natalia Silveira, Timothy Dozat, Marie-Catherine de Marneffe, Samuel R. Bowman, Miriam Connor, John Bauer, and Christopher D. Manning (2014). A gold standard dependency corpus for English. _Proceedings of the Ninth International Conference on Language Resources and Evaluation_, Reykjavík, Iceland, May 26–31, 2014. <http://www.lrec-conf.org/proceedings/lrec2014/pdf/1089_Paper.pdf>

- [10] Nathan Schneider, Emily Danchik, Chris Dyer, and Noah A. Smith. Discriminative lexical semantic segmentation with gaps: running the MWE gamut. _Transactions of the Association for Computational Linguistics_, 2(April):193−206, 2014. http://www.cs.cmu.edu/~ark/LexSem/mwe.pdf

- [11] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, and Martha Palmer. A hierarchy with, of, and for preposition supersenses. _Proceedings of the 9th Linguistic Annotation Workshop_, Denver, Colorado, June 5, 2015. <http://www.cs.cmu.edu/~nschneid/pssts.pdf>

- [12] Nathan Schneider, Dirk Hovy, Anders Johannsen, and Marine Carpuat. SemEval-2016 Task 10: Detecting Minimal Semantic Units and their Meanings (DiMSUM). _Proceedings of the 10th International Workshop on Semantic Evaluation_, San Diego, California, June 16–17, 2016. <http://people.cs.georgetown.edu/nschneid/p/dimsum.pdf>

- [13] King Chan, Julian Brooke, and Timothy Baldwin. Semi-automated resolution of inconsistency for a harmonized multiword expression and dependency parse annotation. _Proceedings of the 13th Workshop on Multiword Expressions_, Valencia, Spain, April 4, 2017. <http://www.aclweb.org/anthology/W17-1726>

- [14] PARSEME Shared Task 1.1 - Annotation guidelines. 2018. <http://parsemefr.lif.univ-mrs.fr/parseme-st-guidelines/1.1/?page=home>

Contact
-------

Questions should be directed to:

Nathan Schneider  
[nathan.schneider@georgetown.edu]()  
http://nathan.cl

History
-------

  - STREUSLE dev:
     * Added streuseval.py, a unified evaluation script for MWEs + supersenses.
     * Added streusvis.py, for viewing sentences with their MWE and supersense annotations.
     * Added supdate.py (sentence-wise) and tupdate.py (token-wise) for editing lexical semantic annotations.
     * Added format conversion scripts conllulex2json.py, conllulex2UDlextag.py, and UDlextag2json.py.
     * Normalized the way MWEs within a sentence are numbered in markup (normalize_mwe_numbering.py).
     * Improvements to govobj.py (issue #35, affecting 184 tokens, plus a small fix in 58db569 which affected 53 tokens).
     * Subdirectories for splits (train/, dev/, test/) now include .json and .govobj.json files alongside the source .conllulex.
     * Added release preparation scripts under releaseutil/.
     * Fixed a very small bug in tquery.py affecting the display of sentence-final matches.
     * Minor corrections in the data and validation improvements.
     * Updated UD parses to the latest dev version (post-v2.4). Among other things, this improves lemmas for words with nonstandard spellings.
  - STREUSLE 4.1: 2018-07-02. Added subtypes to verbal MWEs (871 tokens) per PARSEME Shared Task 1.1 guidelines [14]; some MWE groupings revised in the process.
    Minor improvements to SNACS (preposition/possessive supersense) annotations coordinated with updated guidelines ([5], specifically <https://arxiv.org/abs/1704.02134v3>).
    Implementation of SNACS (preposition/possessive supersense) target identification heuristics from [7].
    New utility scripts for listing/filtering tokens (tquery.py) and converting to and from an Excel-compatible CSV format.
  - STREUSLE 4.0: 2018-02-10. Updated preposition supersenses to new annotation scheme (4398 tokens).
    Annotated possessives (1117 tokens) using preposition supersenses.
    Revised a considerable number of MWEs involving prepositions.
    Added lexical category for every single-word or strong multiword expression.
    New data format (.conllulex) integrates gold syntactic annotations from the Universal Dependencies project.
  - STREUSLE 3.0: 2016-08-23. Added preposition supersenses
  - STREUSLE 2.1: 2015-09-25. Various improvements chiefly to auxiliaries, prepositional verbs; added <code>\`p</code> class label as a stand-in for preposition supersenses to be added in a future release, and <code>\`i</code> for infinitival 'to' where it should not receive a supersense. From 2.0 (not counting <code>\`p</code> and <code>\`i</code>):
    * Annotations have changed for 877 sentences (609 involving changes to labels, 474 involving changes to MWEs).
    * 877 class labels have been changed/added/removed, usually involving a non-supersense label or triggered by an MWE change. Most frequently (118 cases) this was to replace `stative` with the auxiliary label <code>\`a</code>. In only 21 cases was a supersense label replaced with a different supersense label.
  - STREUSLE 2.0: 2015-03-29. Added noun and verb supersenses
  - CMWE 1.0: 2014-03-26. Multiword expressions for 55k words of English web reviews
