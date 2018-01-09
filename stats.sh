#!/bin/bash

echo "STREUSLE Stats" > STATS.md
echo "==============" >> STATS.md
echo "" >> STATS.md
DOCS=`fgrep '# newdoc id' streusle.conllulex | wc -l`
echo "* Documents:     $DOCS" >> STATS.md
SENTS=`fgrep '# sent_id' streusle.conllulex | wc -l`
echo "* Sentences:     $SENTS" >> STATS.md
WORDS=`egrep -v '^$' streusle.conllulex | egrep -v '^#' | fgrep -v 'CopyOf=' | wc -l`
echo "* Tokens:        $WORDS (excludes ellipsis nodes)" >> STATS.md
LEMMAS=`egrep -v '^$' streusle.conllulex | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f3 | sort | uniq | wc -l`
echo "* Unique lemmas: $LEMMAS" >> STATS.md
echo "* [LexCat](LEXCAT.txt)" >> STATS.md
echo "* [MWEs](MWES.txt)" >> STATS.md
echo "* [Supersenses](SUPERSENSES.txt)" >> STATS.md

echo -n "Strong MWEs: " > MWES.txt
SMWES=`egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f13 | fgrep ' ' | wc -l`
printf "%4d\n" "$SMWES" >> MWES.txt

echo -n "Weak MWEs:   " >> MWES.txt
WMWES=`egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f18 | fgrep ' ' | wc -l`
printf "%4d\n" "$WMWES" >> MWES.txt

echo "" >> MWES.txt

echo "Strong MWE token positions" >> MWES.txt
echo "==========================" >> MWES.txt
echo "There are ... MWEs >= ... tokens long:" >> MWES.txt
egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f11 | fgrep ':' | cut -d':' -f2 | sort | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Weak MWE token positions" >> MWES.txt
echo "========================" >> MWES.txt
egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f16 | fgrep ':' | cut -d':' -f2 | sort | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Strong MWEs by LexCat" >> MWES.txt
echo "=====================" >> MWES.txt

egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f12-13 | fgrep ' ' | cut -f1 | sort | uniq -c >> MWES.txt



egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f12 | sort | uniq -c > LEXCAT.txt



egrep -v '^$' streusle.conllulex | egrep -v '^#' | cut -f14-15 | sort | uniq -c > SUPERSENSES.txt

NSS=`cut -f14-15 streusle.conllulex | egrep '^n.' | wc -l`

VSS=`cut -f14-15 streusle.conllulex | egrep '^v.' | wc -l`

PSS=`cut -f14-15 streusle.conllulex | egrep '^p.' | wc -l`

echo "========================" >> SUPERSENSES.txt

echo "$NSS n.*" >> SUPERSENSES.txt
echo "$VSS v.*" >> SUPERSENSES.txt
echo "$PSS p.*" >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "n.* by LexCat" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 streusle.conllulex | fgrep $'\tn.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "v.* by LexCat" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 streusle.conllulex | fgrep $'\tv.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "p.* by LexCat" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 streusle.conllulex | fgrep $'\tp.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt
echo "" >> SUPERSENSES.txt
