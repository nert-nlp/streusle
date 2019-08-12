import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="streusle",
    version="4.1",
    author="Nathan Schneider",
    author_email="nathan.schneider@georgetown.edu",
    description="STREUSLE: a corpus with comprehensive lexical semantic annotation (multiword expressions, supersenses)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nert-nlp/streusle",
    py_modules=["conllulex2csv", "conllulex2UDlextag", "govobj", "lexcatter", "normalize_mwe_numbering",
                "streusvis", "supersenses", "tquery", "UDlextag2json", "conllulex2json",
                "csv2conllulex", "json2conllulex", "mwerender", "psseval", "streuseval", "supdate",
                "tagging", "tupdate"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
