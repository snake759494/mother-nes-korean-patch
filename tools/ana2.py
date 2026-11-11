import sys,collections
from PIL import ImageFont
import engine as E, build as B, make, ins_main, ins_misc, tmpl
texts = ins_main.ko_texts() + ins_misc.ko_texts()+[f[2] for f in tmpl.FREE] + [it[3] for it in tmpl.ITEMS]
G = make.glyph_order(texts, '은는이가을를과와아야으로랑' + tmpl.chars() + tmpl.NAME_SYL)
font=ImageFont.truetype(B.FONT_TTF,8)
pat={}
for ch in G:
    r=B.render_glyph(ch,font); pat.setdefault(r,ch)
R=open('t.nes','rb').read()[16:]
BY={E.glyph_to_bytes(i):c for i,c in enumerate(G)}
def junk(bank):
    a=bank*0x2000+0x1B44; s=set(); n=0
    while n<300:
        c=R[a]
        if c==0: break
        if c==4: a=(a&~0x1FFF)+((R[a+1]|R[a+2]<<8)-0x8000); continue
        if 0x38<=c<=0x3F: s.add(BY.get(R[a:a+2],'')); a+=2
        else:
            s.add(BY.get(R[a:a+1],'')); a+= 3 if c==0x21 else 5 if c==0x23 else 1
        n+=1
    return s
JK={b:junk(b) for b in range(0x18,0x1C)}
jp,ko=ins_main.load_main(); KO={m['id']:ko[m['id']] for m in jp}
SL=set(E.SLOT_TILES)
d=open('cap.bin','rb').read(); REC=4+1+4096+2048
allow=set('가명령말하기조사물건누구와얘기하는거냐'+KO['114E']+KO['3142']+KO['5129'])
bad=0; out=[]
for i in range(0,len(d),REC):
    r=d[i:i+REC]; mid=r[:4].decode().strip(); pg=r[4]; nt=r[5:5+4096]; cr=r[4101:]
    rows=[]; probs=[]
    for y in range(120):
        s=''
        for x in range(32):
            t=nt[y*32+x]
            if t in SL:
                cands=[]
                p=cr[(t-0x80)*16+8:(t-0x80)*16+16]
                if p in pat: cands.append(pat[p])
                if not cands:
                    p=cr[(t-0x80)*16+8:(t-0x80)*16+16]
                    if any(p): s+='▒'
                    else: s+=' '
                else: s+=cands[0]
            else: s+='·'
        h=[k for k,c in enumerate(s) if '가'<=c<='힣']
        if h and '▒' in s[h[0]:h[-1]+1]: probs.append((y,s))
        rows.append(s)
    exp=set(KO[mid])|set('은는이가을를과와아야으로랑좀쯤')|(set('나길') if 'STR' in KO[mid] else set())|allow|JK[(0x30000+int(mid,16))//0x2000]
    seen=set(c for row in rows for c in row if '가'<=c<='힣')
    extra=seen-exp
    if probs or extra:
        bad+=1; out.append((mid,pg,extra,probs[:3],[r for r in rows if any('가'<=c<='힣' or c=='▒' for c in r)]))
import collections;cc=collections.Counter(c for o in out for c in o[2]);print(cc.most_common(40));print(sorted(set(o[0] for o in out)));print('caps',len(d)//REC,'bad',bad)
for o in [o for o in out if o[0] in sys.argv[2:]][:int(sys.argv[1]) if len(sys.argv)>1 else 10]:
    print(o[0],o[1],'extra',o[2],o[3]); print('\n'.join(o[4]))
