import json,re,collections,sys
import engine as E, make, ins_main, ins_misc, tmpl
from enc import Encoder
from charset import decode
texts = ins_main.ko_texts() + ins_misc.ko_texts()+[f[2] for f in tmpl.FREE] + [it[3] for it in tmpl.ITEMS]
g = make.glyph_order(texts, '은는이가을를과와아야으로랑' + tmpl.chars() + tmpl.NAME_SYL)
enc=Encoder(g)
R=open('../Mother (Japan) [한글패치].nes','rb').read()[16:16+0x40000]
O=open('../Mother (Japan).nes','rb').read()[16:16+0x40000]
def L(b):
    c=b[0]
    return 3 if c in(0x21,0x04) else 5 if c==0x23 else 2 if 0x38<=c<=0x3F else 1
def follow(a):
    out=bytearray(); n=0
    while n<4000:
        c=R[a]
        if c==0: return bytes(out)
        if c==4:
            p=R[a+1]|R[a+2]<<8; a=(a&~0x1FFF)+(p-0x8000); continue
        l=L(R[a:]); out+=R[a:a+l]; a+=l; n+=1
    return None
jp,ko=ins_main.load_main(); bad=0
for m in jp:
    if set(m['jp'].replace('\n',''))<=set('。'): continue
    o=0x30000+int(m['id'],16); e=enc.enc(ko[m['id']])
    if follow(o)!=e: bad+=1; print('MISMATCH',m['id'])
print('main checked',len(jp),'bad',bad)
# original GOTO/STR targets into main region that are not message starts
starts={0x30000+int(m['id'],16) for m in jp}
tg=collections.Counter()
for i in range(0x30000,0x37EF6):
    pass
