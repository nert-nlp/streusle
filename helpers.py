class Token:
    def __init__(self, string, conllulex=False):
        self.fields = string.split("\t")
        self.offset, \
            self.word, \
            self.lemma, \
            self.ud_pos, \
            self.ptb_pos, \
            self.morph, \
            self.head, \
            self.deprel = [field if field.strip("_") else None for field in self.fields[:8]] # 1.-8.
        if conllulex:
            self.deps, \
                self.misc, \
                self.smwe, \
                self.lexcat, \
                self.lexlemma, \
                self.ss, \
                self.ss2, \
                self.wmwe, \
                self.wlemma, \
                self.wcat, \
                self.lextag = [field if field.strip("_") else None for field in self.fields[8:19]] # 9.-19.
        self.orig = string
        self.checkmark = ""

class Sentence:
    def __init__(self, tokens, meta):
        self.tokens = tokens
        self.meta = meta
        self.meta_dict = {}
        for meta_info in meta:
            k, v = meta_info.strip("# ").split(" = ")
            self.meta_dict[k] = v

def sentences(filename, conllulex=False):
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
                tokens.append(Token(line, conllulex=conllulex))

    if tokens:
        yield Sentence(tokens, meta)
