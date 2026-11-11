H="をぁぃぅぇぉゃゅょっ◆あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん"
K="ヲァィゥェォャュョッーアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン"
T={}
for i,c in enumerate(H): T[0x86+i]=c
T[0xbe]='|';T[0xbf]='|';T[0xc0]=' ';T[0xc1]='!';T[0xc2]='?';T[0xc3]='ド';T[0xc4]='→';T[0xc5]='▶'
for i,c in enumerate(K): T[0xc6+i]=c
T[0xfe]='゛';T[0xff]='゜'
for i in range(26): T[0x41+i]=chr(65+i)
T[0x40]='$'
for i in range(5): T[0x5b+i]=str(i)
for i in range(5): T[0x7b+i]=str(5+i)
T.update({0x60:',',0x61:'α',0x62:'β',0x63:'γ',0x64:'π',0x65:'Ω',0x66:'_',0x70:'.',0x71:'‥',0x72:'「',0x73:'」',0x74:'(',0x75:')',0x76:'/',0x77:'♪',0x78:'~',0x79:'W',0x7a:'°'})
for t in (0x80,0x81,0x82,0x83,0x84,0x85): T[t]='#'
DK={}
dak_h="がぎぐげござじずぜぞだぢづでど"; dak_k="ガギグゲゴザジズゼゾダヂヅデド"
for i,c in enumerate(dak_h): DK[0x06+i]=c
for i,c in enumerate("ぱぴぷぺぽ"): DK[0x15+i]=c
for i,c in enumerate("ばびぶべぼ"): DK[0x1a+i]=c
DK[0x1f]='ゔ'
for i,c in enumerate(dak_k): DK[0x26+i]=c
for i,c in enumerate("パピプペポ"): DK[0x35+i]=c
for i,c in enumerate("バビブベボ"): DK[0x3a+i]=c
DK[0x3f]='ヴ'
def decode(data,i,stop_at_end=True):
    out=[]
    while i<len(data):
        b=data[i]
        if b>=0x40: out.append(T.get(b,'{%02X}'%b)); i+=1
        elif b in DK: out.append(DK[b]); i+=1
        elif b==0x00: out.append('{END}'); i+=1; 
        elif b in (1,2,3): out.append({1:'\n',2:'{WAIT}',3:'{03}'}[b]); i+=1
        elif b==0x04: out.append('{GOTO %02X%02X}'%(data[i+2],data[i+1])); i+=3
        elif b==0x05: out.append('{05}'); i+=1
        elif b==0x20: out.append('{POS %02X %02X}'%(data[i+1],data[i+2])); i+=3
        elif b==0x21: out.append('{STR %02X%02X}'%(data[i+2],data[i+1])); i+=3
        elif b==0x22: out.append('{REP %02X %02X}'%(data[i+1],data[i+2])); i+=3
        elif b==0x23: out.append('{NUM %02X%02X %02X %02X}'%(data[i+2],data[i+1],data[i+3],data[i+4])); i+=5
        elif b==0x24: out.append('{L|}'); i+=1
        elif b==0x25: out.append('{R|}'); i+=1
        else: out.append('{%02X}'%b); i+=1
        if b==0 and stop_at_end: break
    return ''.join(out),i
