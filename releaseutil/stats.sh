#!/bin/bash
# Arg: .conllulex file, e.g. streusle.conllulex
DATA=$1

echo "STREUSLE Stats" > STATS.md
echo "==============" >> STATS.md
echo "" >> STATS.md
DOCS=`fgrep '# newdoc id' $DATA | wc -l`
echo "* Documents:           $DOCS" >> STATS.md
SENTS=`fgrep '# sent_id' $DATA | wc -l`
echo "* Sentences:           $SENTS" >> STATS.md
WORDS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | wc -l`
echo "* Tokens:              $WORDS (excludes ellipsis nodes)" >> STATS.md
LEMMAS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f3 | sort | uniq | wc -l`
echo "* Unique lemmas:       $LEMMAS" >> STATS.md
LEXTAGS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f19 | sort | uniq | wc -l`
echo "* Unique full lextags: $LEXTAGS" >> STATS.md
echo "* [LexCat](LEXCAT.txt)" >> STATS.md
echo "* [MWEs](MWES.txt)" >> STATS.md
echo "* [Supersenses](SUPERSENSES.txt)" >> STATS.md

echo -n "Strong MWEs: " > MWES.txt
SMWES=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f13 | fgrep ' ' | wc -l`
printf "%4d\n" "$SMWES" >> MWES.txt

echo -n "Weak MWEs:   " >> MWES.txt
WMWES=`egrep -v '^$' $DATA | egrep -v '^#' | cut -f18 | fgrep ' ' | wc -l`
printf "%4d\n" "$WMWES" >> MWES.txt

echo "" >> MWES.txt

echo "MWE Gaps" >> MWES.txt
echo "========" >> MWES.txt
GAPS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f19 | sed -E 's/(.[^-]*)(-.*)?/\1/' | tr '\n' ' ' | egrep -o '[bio][~_]? I[~_]' | wc -l`
SGAPS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f19 | sed -E 's/(.[^-]*)(-.*)?/\1/' | tr '\n' ' ' | egrep -o '[bio][~_]? I_' | wc -l`
WGAPS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f19 | sed -E 's/(.[^-]*)(-.*)?/\1/' | tr '\n' ' ' | egrep -o '[bio][~_]? I~' | wc -l`
MULTIGAPS=`egrep -v '^$' $DATA | egrep -v '^#' | fgrep -v 'CopyOf=' | cut -f19 | sed -E 's/(.[^-]*)(-.*)?/\1/' | tr '\n' ' ' | egrep -o '[bio][~_]? (I_\S* )+[bio]' | wc -l`
echo -n "Strong gaps:   " >> MWES.txt
printf "%4d\n" "$SGAPS" >> MWES.txt
echo -n "Weak gaps:     " >> MWES.txt
printf "%4d\n" "$WGAPS" >> MWES.txt
echo -n "Total gaps:    " >> MWES.txt
printf "%4d\n" "$GAPS" >> MWES.txt
echo -n "Multi-gap MWEs:" >> MWES.txt
printf "%4d\n" "$MULTIGAPS" >> MWES.txt

echo "" >> MWES.txt

echo "Strong MWE token positions" >> MWES.txt
echo "==========================" >> MWES.txt
echo "There are ... MWEs >= ... tokens long:" >> MWES.txt
egrep -v '^$' $DATA | egrep -v '^#' | cut -f11 | fgrep ':' | cut -d':' -f2 | sort | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Weak MWE token positions" >> MWES.txt
echo "========================" >> MWES.txt
egrep -v '^$' $DATA | egrep -v '^#' | cut -f16 | fgrep ':' | cut -d':' -f2 | sort | uniq -c >> MWES.txt

echo "" >> MWES.txt

echo "Strong MWEs by LexCat" >> MWES.txt
echo "=====================" >> MWES.txt

egrep -v '^$' $DATA | egrep -v '^#' | cut -f12-13 | fgrep ' ' | cut -f1 | sort | uniq -c >> MWES.txt



egrep -v '^$' $DATA | egrep -v '^#' | cut -f12 | sort | uniq -c > LEXCAT.txt



egrep -v '^$' $DATA | egrep -v '^#' | cut -f14-15 | sort | uniq -c > SUPERSENSES.txt

NSS=`cut -f14-15 $DATA | egrep '^n.' | wc -l`

VSS=`cut -f14-15 $DATA | egrep '^v.' | wc -l`

PSS=`cut -f14-15 $DATA | egrep '^p.' | wc -l`

echo "========================" >> SUPERSENSES.txt

echo "$NSS n.*" >> SUPERSENSES.txt
echo "$VSS v.*" >> SUPERSENSES.txt
echo "$PSS p.*" >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "n.* by LexCat" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 $DATA | fgrep $'\tn.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "v.* by LexCat" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 $DATA | fgrep $'\tv.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "p.* by LexCat" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 $DATA | fgrep $'\tp.' | cut -f1 | sort | uniq -c >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "p.* by LexCat + construal type" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
# for some bizarre reason, sed and sed -E with a backreference in the pattern don't work here
cut -f12,14-15 $DATA | fgrep $'\tp.' | python3 -c "import fileinput, re
for ln in fileinput.input():
	ln = ln.strip()
	congruent = re.sub(r'(p\.[A-Za-z-]+)\t\1', 'p.X ~> p.X', ln)
	if congruent!=ln: print(congruent)
	else: print(re.sub(r'(p\.[A-Za-z-]+)\tp\.[A-Za-z-]+', 'p.X ~> p.Y', ln))" | sort | uniq -c >> SUPERSENSES.txt

echo "" >> SUPERSENSES.txt
echo "p.* by LexCat + spatiotemporality" >> SUPERSENSES.txt
echo "(TMP = Time|Frequency|Duration|Interval|Temporal, LOC=Locus|Source|Path|Goal|Direction|Extent [not necessarily concrete])" >> SUPERSENSES.txt
echo "========================" >> SUPERSENSES.txt
cut -f12,14-15 $DATA | fgrep $'\tp.' | python3 -c "import fileinput, re
for ln in fileinput.input():
	ln = ln.strip()
	lc, r, f = ln.split('\t')
	if r in ('p.Time', 'p.Frequency', 'p.Duration', 'p.Interval', 'p.Temporal'):
		r = 'p.TMP'
	elif r in ('p.Locus', 'p.Source', 'p.Path', 'p.Goal', 'p.Direction', 'p.Extent'):
		r = 'p.LOC'
	else:
		r = 'p.OTH'
	print(lc, '\t' + r + ' ~> *')" | sort | uniq -c >> SUPERSENSES.txt
echo "" >> SUPERSENSES.txt
