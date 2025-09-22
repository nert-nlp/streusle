import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="streusle",
    version="5.0",
    author="Nathan Schneider",
    author_email="nathan.schneider@georgetown.edu",
    description="STREUSLE: a corpus with comprehensive lexical semantic annotation (multiword expressions, supersenses)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nert-nlp/streusle",
    py_modules=["govobj", "lexcatter",
                "streusvis", "supersenses", "tquery", "UDlextag2json", "conllu2json",
                "json2conllulex", "mwerender", "psseval", "streuseval", "supdate",
                "tagging", "tupdate"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
