Using CoNLL-U-Lex Format Data with Excel
========================================

*Nathan Schneider, 2018-05-28*

One advantage of the tabular data format is that it is conducive to opening as a
spreadsheet. However, spreadsheet editors may mangle the data slightly: 
reading numerals as numeric values and truncating zeros, misinterpreting Unicode 
characters, etc. If you plan to edit the data, it is important to avoid this.

The following workflow has been tested on Microsoft Excel for Mac version 16.13.1; 
it should preserve the data exactly. (Apple Numbers as of 5.0.1 is not recommended 
because it simplifies numeric tokens, e.g. "483.00" to "483", even with quoted CSV input.)

  1. On a Unix/Bash command line, run `./conllulex2csv.py INPUTFILE OUTPUTFILE`, 
	 where INPUTFILE is streusle.conllulex or similar, and OUTPUTFILE is streusle.csv 
	 or similar.

  2. Do not open the CSV file by double-clicking it. Instead, open a blank Excel document.
  
  3. Use File > Import to import the CSV file you created. It will be tab-delimited. 
     On the second page of the import options, __you must select all the columns and 
     specify the Text format for them__.

  4. You should now be able to edit the annotations. Take care to edit only the relevant 
     columns, and not to sort the data or otherwise reorder rows/columns.

  5. To save the modified data, use File > Save As... and choose a new filename.
     Select __CSV UTF-8 (Comma-delimited)__ as the format.

  6. On the command line, run `./csv2conllulex.py INPUTFILE OUTPUTFILE`, 
	 where INPUTFILE is streusle-modified.csv or similar, and OUTPUTFILE is 
	 streusle-modified.conllulex or similar.
	 
  7. Recommended: use the `diff` command line tool to compare your new .conllulex 
     file with the original to make sure there are no extraneous changes.

  8. Run `conllulex2json.py` on the new data to validate it.
