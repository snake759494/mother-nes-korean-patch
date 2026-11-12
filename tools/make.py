import sys, json, re, collections
import engine as E
from enc import Encoder
import build as B
import ins_main, ins_misc, tmpl

PRIORITY = ''   # chars that must be 1-byte (fixed-width templates)
EXTRA_TEXTS = []


def glyph_order(texts, priority):
    c = collections.Counter()
    for t in texts:
        t = re.sub(r'\{(STR|NUM|GOTO)[^}]*\}', '', t)
        for tok in ('으로', '이랑', '이야'): t = t.replace('{%s}' % tok, '으로랑야')
        c.update(ch for ch in t if '가' <= ch <= '힣')
    for a, b in E.JOSA_PAIR:
        c[a] += 10000
        if b: c[b] += 10000
    pri = []
    for ch in priority:
        if '가' <= ch <= '힣' and ch not in pri: pri.append(ch)
    rest = [ch for ch, n in c.most_common() if ch not in pri]
    order = pri + rest
    assert len(pri) <= E.NK1, len(pri)
    assert len(order) < E.NK1 + 7 * 192 + 184, len(order)
    return order


def main(out='../work/test.nes'):
    texts = ins_main.ko_texts() + ins_misc.ko_texts() + EXTRA_TEXTS
    texts += [f[2] for f in tmpl.FREE] + [it[3] for it in tmpl.ITEMS]
    glyphs = glyph_order(texts, '은는이가을를과와아야으로랑' + tmpl.chars() + tmpl.NAME_SYL)
    enc = Encoder(glyphs)
    k1 = glyphs[:E.NK1]
    nm = [c for c in dict.fromkeys(tmpl.NAME_SYL) if c in k1]
    tmpl.GRID[:] = sorted((nm + [c for c in k1 if c not in nm])[:84])
    patches = []
    prg = B.PRG0
    chrp = []
    ins_main.build_main(prg, enc, patches)
    ifree = ins_misc.build_misc(prg, B.CHR0, enc, patches, chrp)
    tmpl.apply(prg, B.CHR0, enc, patches, chrp)
    tmpl.apply_free(prg, B.CHR0, enc, patches, chrp, ifree)
    B.build(glyphs, patches, out, chrp)
    print('glyphs', len(glyphs))


if __name__ == '__main__':
    main(*sys.argv[1:])
