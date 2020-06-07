import sys

class Token:
    def __init__(self, string):
        self.fields = string.split("\t")
        self.offset, \
            self.word, \
            self.lemma, \
            self.ud_pos, \
            self.ptb_pos, \
            self.morph, \
            self.head, \
            self.deprel, \
            self.edeps, \
            self.misc = self.fields[:10]
        self.orig = string

class Sentence:
    def __init__(self, tokens, meta):
        self.tokens = tokens
        self.meta = meta
        self.meta_dict = {}
        for meta_info in meta:
            if ' = ' not in meta_info:
                print('Ignoring comment line:', meta_info, file=sys.stderr)
            else:
                k, v = meta_info.strip("# ").split(" = ")
                self.meta_dict[k] = v

def sentences(filename):
    tokens, meta = [], []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line:
                yield Sentence(tokens, meta)
                tokens = []
                meta = []
            elif line.startswith("#"):
                meta.append(line)
            else:
                tokens.append(Token(line))

    if tokens:
        yield Sentence(tokens, meta)
