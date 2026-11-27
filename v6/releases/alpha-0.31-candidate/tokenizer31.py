"""Bounded deterministic byte-pair tokenizer, trained from scratch."""
from collections import Counter


def merge(seq, pair, token):
    out = []
    i = 0
    while i < len(seq):
        if tuple(seq[i:i+2]) == pair:
            out.append(token)
            i += 2
        else:
            out.append(seq[i])
            i += 1
    return out


class BytePair:
    def __init__(self, merges=()):
        self.merges = tuple(tuple(p) for p in merges)
        if len(self.merges) > 128:
            raise ValueError('merge budget')
        for i, p in enumerate(self.merges):
            if len(p) != 2 or any(type(x) is not int or not 0 <= x < 256+i for x in p):
                raise ValueError('invalid merge')
        if len(set(self.merges)) != len(self.merges):
            raise ValueError('duplicate merge')

    @classmethod
    def train(cls, documents, limit=32):
        if type(limit) is not int or not 0 <= limit <= 128:
            raise ValueError('merge budget')
        seqs = []
        total = 0
        for doc in documents:
            if len(seqs) >= 128 or not isinstance(doc, str) or len(doc) > 65536:
                raise ValueError('document budget')
            seq = list(doc.encode('utf-8'))
            total += len(seq)
            if total > 65536:
                raise ValueError('byte budget')
            seqs.append(seq)
        rules = []
        for i in range(limit):
            counts = Counter(p for s in seqs for p in zip(s, s[1:]))
            if not counts:
                break
            pair = min(counts, key=lambda p: (-counts[p], p))
            if counts[pair] < 2:
                break
            rules.append(pair)
            seqs = [merge(s, pair, 256+i) for s in seqs]
        return cls(rules)

    def encode(self, text):
        if not isinstance(text, str) or len(text) > 65536:
            raise ValueError('input budget')
        seq = list(text.encode('utf-8'))
        if len(seq) > 65536:
            raise ValueError('input budget')
        for i, pair in enumerate(self.merges):
            seq = merge(seq, pair, 256+i)
        return seq

    def decode(self, tokens):
        pieces = [bytes([i]) for i in range(256)]
        for a, b in self.merges:
            if len(pieces[a])+len(pieces[b]) > 65536:
                raise ValueError('expansion budget')
            pieces.append(pieces[a]+pieces[b])
        out = bytearray()
        for t in tokens:
            if type(t) is not int or not 0 <= t < len(pieces):
                raise ValueError('invalid token')
            if len(out)+len(pieces[t]) > 65536:
                raise ValueError('output budget')
            out.extend(pieces[t])
        return out.decode('utf-8')
