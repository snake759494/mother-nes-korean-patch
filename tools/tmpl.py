# fixed-width template replacements: (space, region_start, region_end, jp_run, ko)
# ko is padded with spaces to jp cell width; all ko chars must be 1-byte (PRIORITY)
from charset import T, DK
REV = {v: k for k, v in T.items() if v not in ('#', '|')}
REV.update({v: k for k, v in DK.items()})
REV[' '] = 0xC0

P, C = 'prg', 'chr'
B0 = (0x0430, 0x0590)
B1 = (0x14C9, 0x17ED)
CF = (0x177EC, 0x17A02)
CE = (0x1E800, 0x1ED4A)
ITEMS = [
    # battle command window
    (P, B0, 'たたかう', '싸운다'), (P, B0, 'オート', '자동'), (P, B0, 'ガード', '방어'),
    (P, B0, 'グッズ', '물건'), (P, B1, 'グッズ', '물건'), (P, B0, 'にげる', '도망'), (P, B0, 'チェック', '체크', 2), (P, B1, 'チェック', '조사'), (P, B0, 'うたう', '노래'),
    # field command window
    (P, B1, 'コマンド', '명령'), (P, B1, 'はなす', '말하기'),
    (P, B1, 'だれ', '누구'),
    (P, B1, 'つかう', '사용'), (P, B1, 'たべる', '먹기'), (P, B1, 'わたす', '주기'), (P, B1, 'すてる', '버리기'),
    (P, B1, 'オフェンス', '공격'), (P, B1, 'ティフェンス', '방어'), (P, B1, 'ファイト', '파이트'),
    (P, B1, 'スピード', '스피드'), (P, B1, 'かしこさ', '지혜'), (P, B1, 'たいりょく', '체력'), (P, B1, 'フォース', '포스'),
    # chr: naming confirm / settings
    (C, CF, 'もどる', '뒤로'), (C, CF, 'おわり', '끝'), (C, CF, 'すきなこんだて', '좋아하는 음식'),
    (C, CF, 'これで よろしいですか', '이대로 할까요?'), (C, CF, 'はい  いいえ', '예  아니오'),
    (C, CF, 'メッセージスピード', '대사 속도'), (C, CF, 'はやい ふつう おそい', '빠름  보통  느림'),
    # chr: file select
    (C, CE, 'の きろくを', '의 기록을'), (C, CE, 'けしても よろしいですか?', '지워도 될까요?'),
    (C, CE, 'はい   いいえ', '예   아니오'), (C, CE, 'どこへ うつしますか?', '어디에 옮길까요?'),
    (C, CE, 'ひょうじ', '보기', 3), (C, CE, 'つづき  うつす  けす', '계속   이동   지움'),
    (C, CE, 'ゲームをはじめる', '게임을 시작한다'),
    (C, CE, 'おそい', '느림'), (C, CE, 'ふつう', '보통'), (C, CE, 'はやい', '빠름'),
]


def enc_jp(s):
    if s == 'コマンド': return bytes([REV['コ'], REV['マ'], REV['ン'], 0xC3])
    return bytes(REV[ch] for ch in s)


def chars():
    return ''.join(it[3] for it in ITEMS)


def apply(prg0, chr0, enc, prg_p, chr_p):
    for it in ITEMS:
        sp, (a, b), jp, ko = it[:4]
        cnt = it[4] if len(it) > 4 else 1
        buf = prg0 if sp == P else chr0
        pat = enc_jp(jp)
        assert len(ko) <= len(jp), (jp, ko)
        kb = enc.enc(ko.ljust(len(jp)))
        assert len(kb) == len(pat), (jp, ko, len(kb), len(pat))
        pos = []; i = a
        while True:
            i = buf.find(pat, i, b)
            if i < 0: break
            pos.append(i); i += 1
        assert len(pos) == cnt, (jp, [hex(p) for p in pos])
        for p in pos:
            (prg_p if sp == P else chr_p).append((p, kb))

# free-form END-terminated strings replaced in place: (space, off, ko, overflow_ok)
PROLOGUE = ('1900년대 초\n미국의 시골 마을에 먹구름 같은\n그림자가 드리우고\n한 부부가 행방불명되었습니다.\n'
            '남편의 이름은 조지. 아내는 마리아.\n2년쯤 지나 조지는 집에 돌아왔지만\n'
            '어디서 무엇을 했는지\n누구에게도 말하지 않고\n이상한 연구에 몰두하게 되었습니다.\n'
            '아내 마리아는\n끝내 돌아오지 않았습니다.')
FREE = [
    (P, 0x26DB3, '   예    아니오  '),
    (P, 0x053F, '{20 0D 19}전투 중엔 못 쓴다'),
    (P, 0x0551, '{20 0D 19}전투 중 장비 불가'),
    (P, 0x0565, '{20 0D 19}{STR 0580} 사용불가'),
    (C, 0x17913, PROLOGUE),
    (C, 0x179E6, '1988년 머더스데이 교외'),
    (C, 0x1EB84, '이름을 지어 주세요'),
    (C, 0x1EB91, '여자아이 이름은?'),
    (C, 0x1EB9E, '친구의 이름은?'),
    (C, 0x1EBAB, '또 다른 친구는?'),
    (C, 0x1EBB8, '좋아하는 음식은?'),
    (C, 0x1EBC5, '이 이름은 안 돼'),
    (P, 0x3BE78, '소년A'), (P, 0x3BEB8, '소녀B'), (P, 0x3BEF8, '소년C'), (P, 0x3BF38, '소년D'),
    (P, 0x3BF78, '피피'),
]
NAME_SYL = '소년녀피'
GRID = []   # filled by make: K1 syllables for name grid


def free_chars():
    return ''.join(f[2] for f in FREE) + NAME_SYL


def apply_free(prg0, chr0, enc, prg_p, chr_p, chr_gaps):
    for sp, off, ko in FREE:
        buf = prg0 if sp == P else chr0
        e = buf.index(0, off)
        n = e - off + 1
        by = enc.enc(ko) + b'\x00'
        dst = prg_p if sp == P else chr_p
        if len(by) <= n:
            dst.append((off, by + bytes(n - len(by))))
            continue
        if not (sp == C and 0x17800 <= off < 0x17F32):
            print('FREE OVERFLOW', hex(off), len(by), n, ko); continue
        # GOTO overflow into item-region gaps (SRAM copy at -0x10C00)
        from ins_main import split_lines
        lines = split_lines(by[:-1]); head = b''; k = 0
        while k < len(lines) and len(head) + len(lines[k]) + 3 <= n: head += lines[k]; k += 1
        rest = b''.join(lines[k:]) + b'\x00'
        g = next(g for g in chr_gaps if g[1] - g[0] >= len(rest))
        t = g[0]; g[0] += len(rest)
        ptr = t - 0x10C00
        dst.append((off, head + bytes([0x04, ptr & 0xFF, ptr >> 8]) + bytes(n - len(head) - 3)))
        dst.append((t, rest))
    # name grid: kana strings -> syllables
    syl = list(GRID)
    i = 0x1EC51
    while i < 0x1ED4A:
        e = chr0.index(0, i)
        s = chr0[i:e]
        if s and all(c >= 0x86 or c < 0x40 for c in s if c not in (0xC0, 0xC1, 0xC2)):
            out = bytearray()
            for c in s:
                if c in (0xC1, 0xC2): out.append(c); continue
                ch = syl.pop(0) if syl else ' '
                out += enc.enc(ch)
            assert len(out) == len(s)
            chr_p.append((i, bytes(out)))
        i = e + 1
    # forbidden names -> all '?'
    fb = bytearray(chr0[0x1EBD7:0x1EC51])
    for k, c in enumerate(fb):
        if c not in (0x00, 0xC0): fb[k] = 0xC2
    chr_p.append((0x1EBD7, bytes(fb)))
