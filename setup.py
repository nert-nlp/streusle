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
    py_modules=["conllulex2csv", "conllulex2json", "conllulex2UDlextag", "csv2conllulex",
                "govobj", "json2conllulex", "lexcatter", "mwerender", "normalize_mwe_numbering",
                "psseval", "streuseval", "streusvis", "supersenses", "tagging", "tquery",
                "UDlextag2json"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
