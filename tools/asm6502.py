# Minimal 2-pass 6502 assembler
# syntax: label:  OPC operand ; comment
# directives: .org $addr  .db ...  .dw ...  NAME = expr  .fill n,val
import re
OPS = {}
_tbl = """ADC 69 65 75 -- 6D 7D 79 61 71 -- --
AND 29 25 35 -- 2D 3D 39 21 31 -- --
ASL -- 06 16 -- 0E 1E -- -- -- 0A --
BIT -- 24 -- -- 2C -- -- -- -- -- --
CMP C9 C5 D5 -- CD DD D9 C1 D1 -- --
CPX E0 E4 -- -- EC -- -- -- -- -- --
CPY C0 C4 -- -- CC -- -- -- -- -- --
DEC -- C6 D6 -- CE DE -- -- -- -- --
EOR 49 45 55 -- 4D 5D 59 41 51 -- --
INC -- E6 F6 -- EE FE -- -- -- -- --
JMP -- -- -- -- 4C -- -- -- -- -- 6C
JSR -- -- -- -- 20 -- -- -- -- -- --
LDA A9 A5 B5 -- AD BD B9 A1 B1 -- --
LDX A2 A6 -- B6 AE -- BE -- -- -- --
LDY A0 A4 B4 -- AC BC -- -- -- -- --
LSR -- 46 56 -- 4E 5E -- -- -- 4A --
ORA 09 05 15 -- 0D 1D 19 01 11 -- --
ROL -- 26 36 -- 2E 3E -- -- -- 2A --
ROR -- 66 76 -- 6E 7E -- -- -- 6A --
SBC E9 E5 F5 -- ED FD F9 E1 F1 -- --
STA -- 85 95 -- 8D 9D 99 81 91 -- --
STX -- 86 -- 96 8E -- -- -- -- -- --
STY -- 84 94 -- 8C -- -- -- -- -- --"""
MODES = ['imm', 'zp', 'zpx', 'zpy', 'abs', 'abx', 'aby', 'izx', 'izy', 'acc', 'ind']
for line in _tbl.split('\n'):
    p = line.split()
    OPS[p[0]] = {m: int(v, 16) for m, v in zip(MODES, p[1:]) if v != '--'}
IMP = dict(BRK=0x00, CLC=0x18, CLD=0xD8, CLI=0x58, CLV=0xB8, DEX=0xCA, DEY=0x88, INX=0xE8, INY=0xC8, NOP=0xEA,
           PHA=0x48, PHP=0x08, PLA=0x68, PLP=0x28, RTI=0x40, RTS=0x60, SEC=0x38, SED=0xF8, SEI=0x78, TAX=0xAA,
           TAY=0xA8, TSX=0xBA, TXA=0x8A, TXS=0x9A, TYA=0x98)
BR = dict(BPL=0x10, BMI=0x30, BVC=0x50, BVS=0x70, BCC=0x90, BCS=0xB0, BNE=0xD0, BEQ=0xF0)


class Asm:
    def __init__(self, syms=None):
        self.syms = dict(syms or {})

    def ev(self, s, final):
        s = s.strip()
        if s.startswith('<'): return self.ev(s[1:], final) & 0xFF
        if s.startswith('>'): return (self.ev(s[1:], final) >> 8) & 0xFF
        t = re.sub(r'\$([0-9A-Fa-f]+)', lambda m: str(int(m.group(1), 16)), s)
        t = re.sub(r'%([01]+)', lambda m: str(int(m.group(1), 2)), t)

        def rep(m):
            n = m.group(0)
            if n in self.syms: return str(self.syms[n])
            if final: raise ValueError('undefined symbol ' + n)
            return '0'
        t = re.sub(r'[A-Za-z_][A-Za-z_0-9]*', rep, t)
        return int(eval(t))

    def assemble(self, src, out):
        """out: dict cpuaddr->byte ; returns symbols"""
        lines = []
        for raw in src.split('\n'):
            l = raw.split(';')[0].rstrip()
            if not l.strip(): continue
            lines.append(l)
        for final in (False, False, True):
            pc = 0; res = {}
            for l in lines:
                m = re.match(r'^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=\s*(.+)$', l)
                if m:
                    self.syms[m.group(1)] = self.ev(m.group(2), final); continue
                m = re.match(r'^\s*([A-Za-z_][A-Za-z_0-9]*):(.*)$', l)
                if m:
                    self.syms[m.group(1)] = pc; l = m.group(2)
                    if not l.strip(): continue
                l = l.strip()
                op, _, arg = l.partition(' ')
                op = op.upper(); arg = arg.strip()
                if op == '.ORG': pc = self.ev(arg, final); continue
                if op == '.DB':
                    for a in split_args(arg):
                        if a.startswith('"'):
                            for ch in a[1:-1]: res[pc] = ord(ch); pc += 1
                        else: res[pc] = self.ev(a, final) & 0xFF; pc += 1
                    continue
                if op == '.DW':
                    for a in split_args(arg):
                        v = self.ev(a, final); res[pc] = v & 0xFF; res[pc+1] = (v >> 8) & 0xFF; pc += 2
                    continue
                if op == '.FILL':
                    n, v = split_args(arg)
                    for _ in range(self.ev(n, final)): res[pc] = self.ev(v, final) & 0xFF; pc += 1
                    continue
                if op in IMP and not arg:
                    res[pc] = IMP[op]; pc += 1; continue
                if op in BR:
                    tgt = self.ev(arg, final); d = tgt - (pc + 2)
                    if final and not -128 <= d <= 127: raise ValueError('branch out of range: ' + l)
                    res[pc] = BR[op]; res[pc+1] = d & 0xFF; pc += 2; continue
                if op not in OPS: raise ValueError('bad op ' + l)
                modes = OPS[op]
                if arg in ('', 'A') and 'acc' in modes:
                    res[pc] = modes['acc']; pc += 1; continue
                if arg.startswith('#'):
                    v = self.ev(arg[1:], final); res[pc] = modes['imm']; res[pc+1] = v & 0xFF; pc += 2; continue
                m = re.match(r'^\((.+)\),\s*[Yy]$', arg)
                if m:
                    res[pc] = modes['izy']; res[pc+1] = self.ev(m.group(1), final) & 0xFF; pc += 2; continue
                m = re.match(r'^\((.+),\s*[Xx]\)$', arg)
                if m:
                    res[pc] = modes['izx']; res[pc+1] = self.ev(m.group(1), final) & 0xFF; pc += 2; continue
                m = re.match(r'^\((.+)\)$', arg)
                if m:
                    v = self.ev(m.group(1), final); res[pc] = modes['ind']; res[pc+1] = v & 0xFF; res[pc+2] = v >> 8; pc += 3; continue
                idx = None
                m = re.match(r'^(.+),\s*([XxYy])$', arg)
                if m: arg, idx = m.group(1), m.group(2).upper()
                force_abs = arg.startswith('!')
                if force_abs: arg = arg[1:]
                v = self.ev(arg, final)
                # decide zp vs abs: zp only if value known small and symbol defined (or literal)
                known = all((n in self.syms) for n in re.findall(r'[A-Za-z_][A-Za-z_0-9]*', re.sub(r'\$[0-9A-Fa-f]+', '', arg)))
                zp = (not force_abs) and known and v < 0x100
                if idx is None:
                    mode = 'zp' if zp and 'zp' in modes else 'abs'
                elif idx == 'X':
                    mode = 'zpx' if zp and 'zpx' in modes else 'abx'
                else:
                    mode = 'zpy' if zp and 'zpy' in modes else 'aby'
                    if mode == 'aby' and 'aby' not in modes: mode = 'zpy'
                res[pc] = modes[mode]
                if mode in ('zp', 'zpx', 'zpy'):
                    res[pc+1] = v & 0xFF; pc += 2
                else:
                    res[pc+1] = v & 0xFF; res[pc+2] = (v >> 8) & 0xFF; pc += 3
        out.update(res)
        return self.syms


def split_args(s):
    out = []; cur = ''; q = False
    for ch in s:
        if ch == '"': q = not q
        if ch == ',' and not q: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out
