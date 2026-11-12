import sys, json, os
from PIL import Image, ImageFont, ImageDraw
from asm6502 import Asm
import engine as E

ORIG = '../Mother (Japan).nes'
rom0 = open(ORIG, 'rb').read()
HDR0 = rom0[:16]
PRG0 = rom0[16:16 + 0x40000]
CHR0 = rom0[16 + 0x40000:]

FONT_TTF = 'dl/gal/Galmuri7.ttf'


OVR = {'쯤': bytes.fromhex('00ee44aafe7c447c')}


def render_glyph(ch, font):
    if ch in OVR: return OVR[ch]
    im = Image.new('L', (16, 16), 0)
    ImageDraw.Draw(im).text((0, 0), ch, font=font, fill=255)
    out = []
    for y in range(8):
        b = 0
        for x in range(8):
            if im.getpixel((x, y)) > 127: b |= 0x80 >> x
        out.append(b)
    return bytes(out)


def build(glyph_chars, text_patches, out_path, chr_patches=()):
    """glyph_chars: list of syllables, index = glyph id
       text_patches: list of (prg_offset, bytes) applied on original PRG layout (banks 0..0x1F)"""
    prg = bytearray(PRG0) + bytearray(b'\xff' * 0x40000)
    # copy fixed banks to end
    prg[0x3E * 0x2000:0x40 * 0x2000] = PRG0[0x1E * 0x2000:0x20 * 0x2000]
    for off, data in text_patches:
        prg[off:off + len(data)] = data
        if off >= 0x3C000:   # text in fixed banks -> mirror into new fixed
            prg[off + 0x40000 - 0x0000:off + 0x40000 + len(data)] = data
    # ---- fixed patches ----
    out = {}
    syms = Asm().assemble(E.FIXED, out)
    for a, v in out.items():
        assert 0xC000 <= a <= 0xFFFF
        o = (0x1E * 0x2000) + (a - 0xC000)
        prg[o] = v
        prg[o + 0x40000] = v
    assert syms['TRAMP'] + 0 <= 0xCBFA and syms['REMAP_END'] <= 0xCC21, hex(syms['REMAP_END'])
    assert syms['NH_END'] <= 0xC32A, hex(syms['NH_END'])
    assert syms['FREE_END'] <= 0xFF40, hex(syms['FREE_END'])
    # ---- code bank ----
    cls, rank = E.tables()
    ORIGT = PRG0[0x1E * 0x2000 + 0x2EA:0x1E * 0x2000 + 0x2EA + 64]
    csyms = {'CLASS': 0xB000, 'RANK1': 0xB100, 'ORIGT': 0xB200, 'STATICF': 0xB800}
    cout = {}
    gid = {c: i for i, c in enumerate(glyph_chars)}
    josa = [[], [], [], []]
    for bt, nb in E.JOSA_PAIR:
        g1 = gid[bt]; g2 = gid[nb] if nb else 0xFFFF
        josa[0].append(g1 & 0xFF); josa[1].append(g1 >> 8)
        josa[2].append(g2 & 0xFF); josa[3].append(g2 >> 8)
    csyms.update({'JB': 0xB240, 'JR': 0xB340})
    a = Asm(csyms); s2 = a.assemble(E.code_src(josa), cout)
    cb = bytearray(b'\xff' * 0x2000)
    for ad, v in cout.items():
        assert 0xA000 <= ad < 0xB000, hex(ad)
        cb[ad - 0xA000] = v
    cb[0x1000:0x1100] = bytes(cls)
    cb[0x1100:0x1200] = bytes(rank)
    cb[0x1200:0x1240] = ORIGT
    jb = bytearray(256); jr = bytearray(256)
    for g, ch in enumerate(glyph_chars):
        k = E.batchim(ch)
        if k: jb[g >> 3] |= 1 << (g & 7)
        if k == 2: jr[g >> 3] |= 1 << (g & 7)
    assert len(glyph_chars) <= 2048
    cb[0x1240:0x1340] = jb
    cb[0x1340:0x1440] = jr
    # static font: banks 126/127, with free slots blanked
    sf = bytearray(CHR0[126 * 0x400:128 * 0x400])
    for t in E.SLOT_TILES:
        i = (t - 0x80) * 16
        sf[i:i + 16] = bytes(16)
    cb[0x1800:0x2000] = sf
    prg[E.CODEBANK * 0x2000:(E.CODEBANK + 1) * 0x2000] = cb
    # ---- glyph banks ----
    font = ImageFont.truetype(FONT_TTF, 8)
    for gid, ch in enumerate(glyph_chars):
        g = render_glyph(ch, font)
        o = E.FONTB0 * 0x2000 + gid * 8
        prg[o:o + 8] = g
    assert len(glyph_chars) <= 1024 * 3
    # ---- header: NES 2.0, mapper 191, PRG 512K, CHR 128K, CHR-RAM 2K, PRG-NVRAM 8K
    hdr = bytearray(HDR0)
    hdr[4] = 0x20
    hdr[5] = 0x10
    hdr[6] = (hdr[6] & 0x0F) | 0xF0
    hdr[7] = (hdr[7] & 0x0F) | 0xB0
    hdr[8] = 0x00
    hdr[11] = 0x05
    chrd = bytearray(CHR0)
    for off, d in chr_patches: chrd[off:off + len(d)] = d
    # '.' (code $70): original tile is a centered dot -> bottom period
    o = 125 * 0x400 + 0x30 * 16
    chrd[o:o + 16] = bytes(14) + bytes([0x60, 0x60]) if False else bytes(8) + bytes([0, 0, 0, 0, 0, 0, 0x60, 0x60])
    data = bytes(hdr) + bytes(prg) + bytes(chrd)
    open(out_path, 'wb').write(data)
    return s2


if __name__ == '__main__':
    pass
