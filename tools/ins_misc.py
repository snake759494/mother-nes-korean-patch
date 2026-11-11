import json
from charset import decode
from ins_main import split_lines, place as _place
import ins_main

MISC = None


def misc():
    global MISC
    if MISC is None:
        jp = json.load(open('tr/misc_jp.json', encoding='utf-8'))
        ko = {m['id']: m['ko'] for m in json.load(open('tr/misc_ko.json', encoding='utf-8'))}
        MISC = (jp, ko)
    return MISC


def ko_texts():
    return list(misc()[1].values())


def inplace(buf, a, b, items, out, minhead=None, cpu=0x8000, bank=0x2000, tails=()):
    """items: {off: bytes(no END)} messages located in [a,b) at fixed starts.
       overflow via GOTO into slack gaps. out: list of (off, bytes)."""
    minhead = minhead or {}
    allst = []; i = a
    while i < b:
        allst.append(i); s, j = decode(buf, i); i = j
    nxt = {s: (allst[k + 1] if k + 1 < len(allst) else b) for k, s in enumerate(allst)}
    gl = []
    res = {}
    over = []
    for o, by in items.items():
        e = nxt[o]
        if len(by) + 1 <= e - o:
            res[o] = by + b'\x00'
            if e - (o + len(by) + 1) >= 6: gl.append([o + len(by) + 1, e])
        else:
            over.append((o, e, by))
    for t in tails: gl.append(list(t))
    over.sort(key=lambda x: (-max(map(len, split_lines(x[2]))), -len(x[2])))
    fails = []
    # ins_main.place uses BASE for pointer calc; emulate with offset shift
    for o, e, by in over:
        lines = split_lines(by)
        kmax = 0; hl = 0
        while kmax < len(lines) and hl + len(lines[kmax]) + 3 <= e - o:
            hl += len(lines[kmax]); kmax += 1
        ok = False
        for k in range(kmax, minhead.get(o, 0) - 1, -1):
            head = b''.join(lines[:k])
            save = [g[:] for g in gl]; tmp = {}
            gl.append([o + len(head) + 3, e])
            tgt = place2(gl, lines[k:], tmp, cpu, bank)
            if tgt is not None:
                ok = True; res.update(tmp)
                ptr = cpu + (tgt % bank)
                res[o] = head + bytes([0x04, ptr & 0xFF, ptr >> 8])
                break
            gl[:] = save
        if not ok: fails.append(o)
    for o, by in res.items(): out.append((o, by))
    return fails, sum(g[1] - g[0] for g in gl)


def place2(gaps, lines, out, cpu, bank):
    need = sum(map(len, lines)) + 1
    fr = sorted(gaps, key=lambda g: g[1] - g[0])
    g = next((g for g in fr if g[1] - g[0] >= need), None)
    if g is not None:
        t = g[0]; g[0] += need
        out[t] = b''.join(lines) + b'\x00'
        return t
    g = next((g for g in fr if g[1] - g[0] >= len(lines[0]) + 3), None)
    if g is None: return None
    head = bytearray(); k = 0
    while k < len(lines) and len(head) + len(lines[k]) + 3 <= g[1] - g[0]:
        head += lines[k]; k += 1
    if k == 0: return None
    t = g[0]; g[0] += len(head) + 3
    nt = place2(gaps, lines[k:], out, cpu, bank)
    if nt is None: return None
    ptr = cpu + (nt % bank)
    out[t] = bytes(head) + bytes([0x04, ptr & 0xFF, ptr >> 8])
    return t


def pack(regions, names, pinned=None, slots=None):
    """regions: list of [a,b). names: list of (key, bytes incl END). pinned: {key: offset}
       slots: {key: end} max end for pinned. returns pos, patches, free list"""
    pinned = pinned or {}; slots = slots or {}
    used = []; pos = {}; patches = []
    for k, by in names:
        if k in pinned:
            o = pinned[k]
            if k in slots: assert o + len(by) <= slots[k], 'pinned overflow %X (%d>%d)' % (k, len(by), slots[k] - o)
            pos[k] = o; used.append((o, o + len(by))); patches.append((o, by))
    used.sort()
    free = []
    for a, b in regions:
        cur = a
        for s, e in used:
            if e <= a or s >= b: continue
            if s > cur: free.append([cur, s])
            cur = max(cur, e)
        if cur < b: free.append([cur, b])
    for k, by in sorted(names, key=lambda x: -len(x[1])):
        if k in pos: continue
        g = min((g for g in free if g[1] - g[0] >= len(by)), key=lambda g: g[1] - g[0], default=None)
        assert g, 'pack overflow %r need %d' % (k, len(by))
        pos[k] = g[0]; patches.append((g[0], by)); g[0] += len(by)
    return pos, patches, free


def build_misc(prg0, chr0, enc, prg_p, chr_p):
    jp, ko = misc()
    J = {m['id']: m for m in jp}
    def E(i): return enc.enc(ko[i])
    # ---- enemy names (bank 0, ptrs in bank 0x16 records) ----
    ids = [m['id'] for m in jp if m['id'].startswith('enemy:')]
    names = [(int(i[6:], 16), E(i) + b'\x00') for i in ids]
    # include empty name at 0x0001 (ptr 8001) untouched
    pos, pt, efree = pack([(0x0002, 0x02A5)], names); fr = sum(g[1]-g[0] for g in efree)
    for o in range(0x0002, 0x02A5): prg_p.append((o, b'\x00'))
    prg_p += pt
    for n in range(122):
        o = 0x2C000 + 32 * n + 0x18
        p = prg0[o] | prg0[o + 1] << 8
        if p - 0x8000 in pos:
            q = 0x8000 + pos[p - 0x8000]
            prg_p.append((o, bytes([q & 0xFF, q >> 8])))
        elif 0x8002 <= p < 0x82A5:
            prg_p.append((o, bytes([0x01, 0x80])))
    print('enemy free', fr)
    # ---- battle messages (bank 0, in place + GOTO) ----
    bids = sorted((i for i in ko if i.startswith('battle:')), key=lambda i: int(i[7:], 16))
    starts = [int(i[7:], 16) for i in bids]
    ends = starts[1:] + [0x14C9]
    def ctlpos(by):
        """list of byte offsets right after each 01/02/03 control"""
        r = []; i = 0
        while i < len(by):
            c = by[i]
            n = 3 if c in (0x21, 0x04) else 5 if c == 0x23 else 2 if 0x38 <= c <= 0x3F else 1
            i += n
            if c in (1, 2, 3): r.append(i)
        return r
    # refs: table words + STR operands inside battle text
    refs = []
    for k in range(0x780, 0x8D2, 2):
        v = prg0[k] | prg0[k + 1] << 8
        if 0x88DF <= v < 0x94C9: refs.append(k)
    def anchor(off):
        for s0, e0 in zip(starts, ends):
            if s0 <= off < e0:
                if off == s0: return s0, 0
                cp = ctlpos(prg0[s0:e0])
                assert (off - s0) in cp, 'anchor mid %X' % off
                return s0, cp.index(off - s0) + 1
        raise ValueError(hex(off))
    # encode with placeholder STR values (length stable)
    raw = {s0: ko['battle:%05X' % s0] for s0 in starts}
    enc0 = {s0: E('battle:%05X' % s0) for s0 in starts}
    names = [(s0, enc0[s0] + b'\x00') for s0 in starts]
    regs = [(0x08DF, 0x14C8)] + [tuple(g) for g in efree if g[1] - g[0] > 2]
    pos, pt, bfree = pack(regs, names)
    def newaddr(off):
        if off == 0x14C8: return 0x94C8
        s0, n = anchor(off)
        base = pos[s0]
        if n == 0: return 0x8000 + base
        cp = ctlpos(enc0[s0])
        return 0x8000 + base + cp[n - 1]
    # re-encode with fixed STR pointers into bank0 battle text
    import re as _re
    for s0 in starts:
        t = raw[s0]
        def rp(m):
            v = int(m.group(1), 16)
            if 0x88DF <= v < 0x94C9: return '{STR %04X}' % newaddr(v - 0x8000)
            return m.group(0)
        t2 = _re.sub(r'\{STR ([0-9A-F]{4})\}', rp, t)
        by = enc.enc(t2) + b'\x00'
        assert len(by) == len(enc0[s0]) + 1
        prg_p.append((pos[s0], by)) if False else None
        enc0[s0] = by[:-1]
    for o in range(0x08DF, 0x14C9): prg_p.append((o, b'\x00'))
    for s0 in starts: prg_p.append((pos[s0], enc0[s0] + b'\x00'))
    for k in refs:
        v = prg0[k] | prg0[k + 1] << 8
        q = newaddr(v - 0x8000); prg_p.append((k, bytes([q & 0xFF, q >> 8])))
    fails = []
    print('battle free', sum(g[1] - g[0] for g in bfree), 'refs', len(refs))
    # ---- item/psi/place/status names (CHR, copied to $6800) ----
    ids = [m['id'] for m in jp if m['id'].startswith('item:')]
    names = [(int(i[5:], 16), E(i) + b'\x00') for i in ids]
    import engine as EN
    hole = 0x17F32 - EN.SRHOLE
    EN.SRBASE = hole - 0x10C00
    pinned = {}; slots = {}; alias = {}
    pos, pt, ifree = pack([(0x17A02, hole)], names, pinned, slots)
    for k, t in alias.items(): pos[k] = pos[t]; fr = sum(g[1]-g[0] for g in ifree)
    for o in range(0x17A02, 0x17F32): chr_p.append((o, b'\x00'))
    chr_p += pt
    refs = list(range(0x1800, 0x1FB8, 8))
    for r in refs:
        p = prg0[r] | prg0[r + 1] << 8
        o = p + 0x10C00
        if o in pos:
            q = pos[o] - 0x10C00; prg_p.append((r, bytes([q & 0xFF, q >> 8])))
        elif 0x17A02 <= o < 0x17F32:
            prg_p.append((r, bytes([0x01, 0x6E])))
    for r in range(0x3C809, 0x3C819, 2):
        p = prg0[r] | prg0[r + 1] << 8
        o = p + 0x10C00
        if o in pos:
            q = pos[o] - 0x10C00; prg_p.append((r, bytes([q & 0xFF, q >> 8])))
    print('item free', fr)
    return ifree
