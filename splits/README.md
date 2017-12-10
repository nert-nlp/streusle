STREUSLE Data Splits
====================

This directory contains train/test splits for experiments conducted on this corpus.
Each sentence is assigned to either train or test. Files in this directory
list the sentence IDs.

- mwe-train.sentids, mwe-test.sentids: This partitioning of the sentences was used in the experiments for MWE identification in [1] and joint MWE and noun+verb supersense tagging in [2]. Note, however, that those papers used earlier versions of the corpus: CMWE 1.0 in [1] and STREUSLE 2.0 in [2]. The relevant annotations will be slightly different in this release. To replicate the earlier experiments, download the earlier releases at http://www.cs.cmu.edu/~ark/LexSem/.

- psst-test.sentids: Recommended test set for preposition supersense experiments, as explained in section 3.4 of [3]. Sentences whose IDs are not listed in this file belong to the recommended training set.

References:

- [1] Nathan Schneider, Emily Danchik, Chris Dyer, and Noah A. Smith. Discriminative lexical semantic segmentation with gaps: running the MWE gamut. _Transactions of the Association for Computational Linguistics_, 2(April):193−206, 2014. http://www.cs.cmu.edu/~ark/LexSem/mwe.pdf

- [2] Nathan Schneider and Noah A. Smith. A corpus and model integrating multiword expressions and supersenses. _Proceedings of the 2015 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies_, Denver, Colorado, May 31–June 5, 2015. <http://www.cs.cmu.edu/~nschneid/sst.pdf>

- [3] Nathan Schneider, Jena D. Hwang, Vivek Srikumar, Meredith Green, Abhijit Suresh, Kathryn Conger, Tim O'Gorman, and Martha Palmer. A corpus of preposition supersenses. _Proceedings of the 10th Linguistic Annotation Workshop_, Berlin, Germany, August 11, 2016. <http://www.cs.cmu.edu/~nschneid/psstcorpus.pdf>
