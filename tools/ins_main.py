# main dialogue insertion: in-place with GOTO overflow into gaps in the same bank
import json, re
from charset import decode
BASE = 0x30000
END = 0x37EF6


def load_main():
    jp, ko = [], {}
    for k in range(8):
        jp += json.load(open('tr/main_%d.json' % k, encoding='utf-8'))
        for m in json.load(open('tr/ko_%d.json' % k, encoding='utf-8')):
            ko[m['id']] = m['ko']
    return jp, ko


def ko_texts():
    jp, ko = load_main()
    return list(ko.values())


def split_lines(b):
    """split encoded bytes (without END) into chunks ending after 01/03 control (line starts)"""
    out = []; cur = bytearray(); i = 0
    while i < len(b):
        c = b[i]
        if c in (0x21, 0x04): n = 3
        elif c == 0x23: n = 5
        elif 0x38 <= c <= 0x3F: n = 2
        else: n = 1
        cur += b[i:i + n]; i += n
        if c in (0x01, 0x03):
            out.append(bytes(cur)); cur = bytearray()
    if cur: out.append(bytes(cur))
    return out


def place(gaps, lines, out):
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
    nt = place(gaps, lines[k:], out)
    if nt is None: return None
    ptr = 0x8000 + ((BASE + nt) % 0x2000)
    out[t] = bytes(head) + bytes([0x04, ptr & 0xFF, ptr >> 8])
    return t


def build_main(prg_orig, enc, patches):
    jp, ko = load_main()
    starts = sorted(int(m['id'], 16) for m in jp)
    # all message starts including empty ones: scan raw
    raw = prg_orig[BASE:END]
    allst = []; i = 0
    while i < len(raw):
        allst.append(i); s, j = decode(raw, i); i = j
    nxt = {s: (allst[k + 1] if k + 1 < len(allst) else len(raw)) for k, s in enumerate(allst)}
    msgs = []
    for m in jp:
        o = int(m['id'], 16)
        t = ko[m['id']]
        if set(m['jp'].replace('\n', '')) <= set('。'):
            continue  # filler: keep original
        b = enc.enc(t)
        msgs.append((o, nxt[o], b))
    # gaps: per bank
    bankfree = {}
    def addfree(a, b):
        if b - a >= 6: bankfree.setdefault((BASE + a) // 0x2000, []).append([a, b])
    # first pass: fits?
    over = []
    out = {}
    for o, e, b in msgs:
        bk = (BASE + o) // 0x2000
        assert (BASE + e - 1) // 0x2000 == bk, hex(o)
        if len(b) + 1 <= e - o:
            out[o] = b + b'\x00'; addfree(o + len(b) + 1, e)
        else:
            over.append((o, e, b))
    # bank tail free: original ff runs at end of each bank
    for bk in range(0x18, 0x1C):
        a = bk * 0x2000 - BASE; z = a + 0x2000
        t = z
        while t > a and prg_orig[BASE + t - 1] == 0xFF: t -= 1
        if z - t > 2: addfree(t + 1, z)
    # overflow placement
    over.sort(key=lambda x: (-max(map(len, split_lines(x[2]))), -len(x[2])))
    fails = 0
    for o, e, b in over:
        bk = (BASE + o) // 0x2000
        lines = split_lines(b)
        # head: fill slot; try fewer head lines if needed
        kmax = 0; hl = 0
        while kmax < len(lines) and hl + len(lines[kmax]) + 3 <= e - o:
            hl += len(lines[kmax]); kmax += 1
        ok = False
        gl = bankfree.setdefault(bk, [])
        for k in range(kmax, -1, -1):
            head = b''.join(lines[:k])
            save = [g[:] for g in gl]; tmp = {}
            gl.append([o + len(head) + 3, e])
            tgt = place(gl, lines[k:], tmp)
            if tgt is not None:
                ok = True; out.update(tmp)
                ptr = 0x8000 + ((BASE + tgt) % 0x2000)
                out[o] = head + bytes([0x04, ptr & 0xFF, ptr >> 8])
                break
            gl[:] = save
        if not ok:
            fails += 1; print('NOFIT %05X' % o)
    for o, b in out.items():
        patches.append((BASE + o, b))
    tot = {bk: sum(g[1] - g[0] for g in v) for bk, v in bankfree.items()}
    print('main: msgs %d overflow %d fails %d free %s' % (len(msgs), len(over), fails, tot))
    return fails
