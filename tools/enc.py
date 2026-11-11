import engine as E

# non-korean characters -> original codes
SYM = {' ': 0xC0, '!': 0xC1, '?': 0xC2, '◆': 0x90, '.': 0x70, ',': 0x60, '…': 0x71, '‥': 0x71,
       '「': 0x72, '」': 0x73, '(': 0x74, ')': 0x75, '/': 0x76, '♪': 0x77, '-': 0xD0, 'ー': 0xD0,
       '~': 0x78, '°': 0x7A, '。': 0xFF, '$': 0x40, 'α': 0x61, 'β': 0x62, 'γ': 0x63, 'π': 0x64, 'Ω': 0x65,
       '→': 0xC4, '▶': 0xC5, '\'': 0x60}
for i in range(26): SYM[chr(65 + i)] = 0x41 + i
for i in range(5): SYM[str(i)] = 0x5B + i
for i in range(5): SYM[str(5 + i)] = 0x7B + i
JT = {'은': [0], '이': [1], '을': [2], '과': [3], '아': [4], '으로': [5, '로'], '이랑': [6, '랑'], '이야': [6, '야']}
CTRL = {'WAIT': 0x02, '03': 0x03, 'L|': 0x24, 'R|': 0x25, 'n': 0x01, 'w': 0x02, 'p': 0x03, 'e': 0x00}


def is_hangul(ch):
    return 0xAC00 <= ord(ch) <= 0xD7A3


class Encoder:
    def __init__(self, glyphs):
        self.gid = {c: i for i, c in enumerate(glyphs)}

    def enc(self, s):
        """s: text with {..} escapes: {n} newline {p} 03 {w} 02 {e} 00, {hh hh..} raw hex"""
        out = bytearray(); i = 0
        while i < len(s):
            ch = s[i]
            if ch == '{':
                j = s.index('}', i)
                tok = s[i + 1:j]
                if tok.startswith('STR '):
                    v = int(tok[4:], 16); out += bytes([0x21, v & 0xFF, v >> 8])
                elif tok.startswith('NUM '):
                    p = tok[4:].split(); v = int(p[0], 16)
                    out += bytes([0x23, v & 0xFF, v >> 8, int(p[1], 16), int(p[2], 16)])
                elif tok.startswith('GOTO '):
                    v = int(tok[5:], 16); out += bytes([0x04, v & 0xFF, v >> 8])
                elif tok in CTRL: out.append(CTRL[tok])
                elif tok in JT:
                    for t in JT[tok]:
                        if isinstance(t, int): out += bytes([0x3F, 0xF8 + t])
                        else: out += E.glyph_to_bytes(self.gid[t])
                else: out += bytes.fromhex(tok)
                i = j + 1; continue
            if ch == '\n': out.append(1); i += 1; continue
            if is_hangul(ch): out += E.glyph_to_bytes(self.gid[ch])
            elif ch.upper() in SYM and ch.isalpha(): out.append(SYM[ch.upper()])
            elif ch in SYM: out.append(SYM[ch])
            else: raise ValueError('unencodable %r in %r' % (ch, s))
            i += 1
        return bytes(out)
