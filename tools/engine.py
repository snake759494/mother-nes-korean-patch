# Korean dynamic-font engine for MOTHER (J) - assembly sources
CODEBANK = 0x20      # 8KB bank mapped at $A000
FONTB0 = 0x21        # glyph banks mapped at $8000 (1024 glyphs each)

NSLOT = 108
SRHOLE = 217          # bytes reserved in SRAM text copy
SRBASE = 0           # set by build
# free tiles in font area (former kana)
FREE_TILES = list(range(0x86, 0x90)) + list(range(0x91, 0xBE)) + list(range(0xC6, 0xD0)) + list(range(0xD1, 0xFE)) + [0xC3]
SLOT_TILES = FREE_TILES[:NSLOT]

# 1-byte korean codes (155)
K1_CODES = list(range(0x06, 0x20)) + list(range(0x26, 0x38)) + list(range(0x86, 0x90)) + list(range(0x91, 0xBE)) + [0xC3] + list(range(0xC6, 0xD0)) + list(range(0xD1, 0xFE))
NK1 = len(K1_CODES)
PREFIXES = list(range(0x38, 0x40))   # 2-byte: prefix + (0x40..0xFF)
SECOND_BASE = 0x40
NSECOND = 0x100 - SECOND_BASE      # 192


def glyph_to_bytes(gid):
    """glyph id -> encoded bytes"""
    if gid < NK1:
        return bytes([K1_CODES[gid]])
    g = gid - NK1
    p, s = divmod(g, NSECOND)
    return bytes([PREFIXES[p], SECOND_BASE + s])


COMMON = f"""
CODEBANK = ${CODEBANK:02X}
FONTB0 = ${FONTB0:02X}
NSLOT = {NSLOT}
IDLO = SRBASE
IDHI = SRBASE+108
MAGIC = SRBASE+216
QTILE = $0101
QLO = $0109
QHI = $0111
T2 = $0119
T3 = $011A
LASTB = $011B
T4 = $011C
CLK = $011D
QH = $011E
QT = $011F
ZA = $0120
ZF = $0121
ZC = $0122
T0 = $0123
T1 = $0124
STAMP = $0130
PSEL = $0125
"""

FIXED = "SRBASE = $0000" + COMMON + """
; ---- decoder entry replacements ----
.org $CBDC
CBDC_:  STA ZA
        LDA #$00
TRAMP:  STA ZF
        TXA
        PHA
        LDA $F7
        PHA
        LDA #CODEBANK
        LDX #$07
        JSR $FFD0
        JSR $A000
        PLA
        LDX #$07
        JMP TRAMP2
.org $CBFB
CBFB_:  STA ZA
        LDA #$01
        BNE TRAMP
TRAMP2: JSR $FFD0
        PLA
        TAX
        LDY $7A
        LDA ZC
        LSR A
        LDA ZA
        RTS
REMAP:  CMP #$7E
        BCC REM1
        CMP #$80
        BCS REM1
        ADC #$02
REM1:   STA $F0,X
        TXA
        RTS
REMAP_END:

.org $FFD2
        JSR REMAP

; ---- NMI hook / init (old C2EA table area) ----
.org $C2EA
NH:     LDA QH
        CMP QT
        BEQ NHQ
        LDA #$07
        ORA $EF
        STA $8000
        LDA #CODEBANK
        STA $8001
        JSR $A003
        LDA #$07
        ORA $EF
        STA $8000
        LDA $F7
        STA $8001
        LDY $E6
        PLA
        PLA
        JMP $F8D8
NHQ:    LDY $E6
        LDA $E0
        RTS
INIT:   LDA #CODEBANK
        LDX #$07
        JSR $FFD0
        JSR $A006
        JMP $FDA0
NH_END:
.org $FF0A
NUMLO:  PHA
        LDA #$64
        STA PSEL
        PLA
        JMP $CBDC
NUMUP:  PHA
        LDA #$64
        STA PSEL
        PLA
        JMP $CBFB
FREE_END:

.org $CB2B
        JSR NUMLO
.org $CB34
        JSR NUMUP

.org $F8A9
        JSR NH
        NOP
.org $FFAB
        JSR INIT
"""


def code_src(josa):
    jl = [','.join('$%02X' % v for v in row) for row in josa]
    return ("SRBASE = $%04X" % SRBASE) + COMMON + f"""
NK1 = {NK1}
.org $A000
        JMP DECODE
        JMP NMIUP
        JMP RINIT

; ---------- decoder ----------
DECODE: INY
        STY $7A
        LDA MAGIC
        CMP #$A5
        BEQ DM
        JSR TINIT
DM:        LDA $F4
        CMP #$80
        BEQ DK
        JMP ORIGD
DK:     LDX ZA
        LDA CLASS,X
        AND #$0F
        BNE DK1
        JMP PLAIN
DK1:    CMP #$03
        BNE DK2
        JMP CTL
DK2:    CMP #$02
        BEQ KOR2
        LDA RANK1,X
        STA T0
        LDA #$00
        STA T1
        JMP KORC
KOR2:   LDA PSEL
        BEQ K2A
        LDA ($64),Y
        JMP K2B
K2A:    LDA ($74),Y
K2B:    INC $7A
        CPX #$3F
        BNE K2N
        CMP #$F8
        BCC K2N
        JMP JOSA
K2N:    SEC
        SBC #$40
        STA T0
        TXA
        SEC
        SBC #$38
        TAX
        CLC
        LDA T0
        ADC P192LO,X
        STA T0
        LDA P192HI,X
        ADC #$00
        STA T1
KORC:   JSR SETB
        LDA ZF
        BNE UPK
        JSR CACHE
        JMP RETC
UPK:    LDA #$C0
RETC:   STA ZA
        LDA #$01
        STA ZC
        LDA #$00
        STA PSEL
        RTS
PLAIN:  LDA CLASS,X
        AND #$30
        CMP #$30
        BEQ PL2
        LSR A
        LSR A
        LSR A
        LSR A
        STA LASTB
PL2:    LDA ZF
        BEQ PLLO
        LDA #$C0
        BNE RETC
PLLO:   TXA
        JMP RETC
CTL:    LDA ORIGT,X
        CMP #$0A
        BCC CTL0
        ORA #$B0
        JMP RETC
CTL0:   STA ZA
        LDA #$00
        STA ZC
        STA PSEL
        RTS
; josa: A = $F8+idx
JOSA:   SEC
        SBC #$F8
        TAX
        LDA LASTB
        BEQ JN
        CMP #$01
        BEQ JBT
        CPX #$05
        BEQ JN
JBT:    LDA JBLO,X
        STA T0
        LDA JBHI,X
        JMP JGO
JN:     LDA JNLO,X
        STA T0
        LDA JNHI,X
JGO:    STA T1
        CMP #$FF
        BEQ JSKIP
        JMP KORC
JSKIP:  LDA #$05
        JMP CTL0
; set LASTB from glyph id T0/T1
SETB:   LDA T0
        AND #$07
        TAY
        LDA T1
        STA T2
        LDA T0
        LSR T2
        ROR A
        LSR T2
        ROR A
        LSR T2
        ROR A
        TAX
        LDA JB,X
        AND BITM,Y
        BEQ SB0
        LDA JR,X
        AND BITM,Y
        BEQ SB1
        LDA #$02
        BNE SBS
SB1:    LDA #$01
        BNE SBS
SB0:    LDA #$00
SBS:    STA LASTB
        RTS
BITM:   .db $01,$02,$04,$08,$10,$20,$40,$80
; original decoder (non-font screens)
ORIGD:  LDA ZA
        CMP #$40
        BCS OHI
        TAX
        LDA ORIGT,X
        CMP #$80
        BCS ODK
        CMP #$20
        BCS OHD
        CMP #$0A
        BCS OSM
        JMP CTL0
OSM:    ORA #$B0
        JMP RETC
ODK:    LDX ZF
        BEQ ORT
        LDA #$FE
        BNE ORT
OHD:    LDX ZF
        BNE OH1
        ORA #$80
        JMP RETC
OH1:    LDA #$FF
        BNE ORT
OHI:    LDX ZF
        BEQ ORT
        LDA #$C0
ORT:    JMP RETC

; ---------- glyph cache (clock) ----------
CACHE:  LDX #NSLOT-1
CS1:    LDA IDLO,X
        CMP T0
        BNE CSN
        LDA IDHI,X
        CMP T1
        BEQ CHIT
CSN:    DEX
        BPL CS1
; miss: LRU victim (max age, ages clamped to 200)
        INC CLK
        LDA #$00
        STA T2
        STA T4
        LDX #NSLOT-1
CL1:    LDA CLK
        SEC
        SBC STAMP,X
        CMP #200
        BCC CL2
        LDA CLK
        SEC
        SBC #200
        STA STAMP,X
        LDA #200
CL2:    CMP T2
        BCC CL3
        STA T2
        STX T4
CL3:    DEX
        BPL CL1
        LDX T4
        LDA CLK
        STA STAMP,X
        LDA #$80
        STA $A001
        LDA T0
        STA IDLO,X
        LDA T1
        STA IDHI,X
        LDA #$C0
        STA $A001
        LDA SLOTT,X
        STA T2
        JMP ENQ
CHIT:   LDA CLK
        STA STAMP,X
        LDA SLOTT,X
        RTS
; enqueue T2 (tile) with id T0/T1
ENQ:    LDA QT
        CLC
        ADC #$01
        AND #$07
        CMP QH
        BNE ROOM
        LDA $FF
        BMI ENQ
        JSR DFLUSH
        JMP ENQ
ROOM:   LDX QT
        LDA T2
        STA QTILE,X
        LDA T0
        STA QLO,X
        LDA T1
        STA QHI,X
        TXA
        CLC
        ADC #$01
        AND #$07
        STA QT
        LDA $FF
        BMI ENQD
        JSR DFLUSH
ENQD:   LDA T2
        RTS

; direct flush (NMI disabled): poll vblank for each glyph
DFLUSH: LDA QH
        CMP QT
        BEQ DFE
DFW:    BIT $2002
        BPL DFW
        LDA #$01
        STA T3
        JSR UPCORE
        LDA $FC
        STA $2005
        LDA $FD
        STA $2005
        LDA $FF
        STA $2000
        JMP DFLUSH
DFE:    LDA $EE
        ORA $EF
        STA $8000
        RTS

; NMI upload, max 4 glyphs
NMIUP:  LDA #$04
        STA T3
UPCORE: LDA $00
        PHA
        LDA $01
        PHA
        LDA #$04
        ORA $EF
        STA $8000
        LDA #$80
        STA $8001
        LDA #$05
        ORA $EF
        STA $8000
        LDA #$81
        STA $8001
UPL:    LDY QH
        CPY QT
        BEQ UPF
        LDA QHI,Y
        LSR A
        LSR A
        CLC
        ADC #FONTB0
        TAX
        LDA #$06
        ORA $EF
        STA $8000
        STX $8001
        LDA QLO,Y
        STA $00
        LDA QHI,Y
        AND #$03
        STA $01
        ASL $00
        ROL $01
        ASL $00
        ROL $01
        ASL $00
        ROL $01
        LDA $01
        ORA #$80
        STA $01
        BIT $2002
        LDA QTILE,Y
        LSR A
        LSR A
        LSR A
        LSR A
        BIT $EF
        BMI UPI
        ORA #$10
UPI:    STA $2006
        LDA QTILE,Y
        ASL A
        ASL A
        ASL A
        ASL A
        STA $2006
        LDA #$00
        LDX #$08
UPZ:    STA $2007
        DEX
        BNE UPZ
        LDY #$00
UPD:    LDA ($00),Y
        STA $2007
        INY
        CPY #$08
        BNE UPD
        LDA QH
        CLC
        ADC #$01
        AND #$07
        STA QH
        DEC T3
        BNE UPL
UPF:    LDA #$04
        ORA $EF
        STA $8000
        LDA $F4
        STA $8001
        LDA #$05
        ORA $EF
        STA $8000
        LDA $F5
        STA $8001
        LDA #$06
        ORA $EF
        STA $8000
        LDA $F6
        STA $8001
        PLA
        STA $01
        PLA
        STA $00
        RTS

; ---------- reset init ----------
RINIT:  LDA #$00
        STA $2001
        LDA #$04
        ORA $EF
        STA $8000
        LDA #$80
        STA $8001
        LDA #$05
        ORA $EF
        STA $8000
        LDA #$81
        STA $8001
        BIT $2002
        LDA #$08
        BIT $EF
        BMI RI1
        LDA #$18
RI1:    STA $2006
        LDA #$00
        STA $2006
        LDA #<STATICF
        STA $00
        LDA #>STATICF
        STA $01
        LDX #$08
        LDY #$00
RI2:    LDA ($00),Y
        STA $2007
        INY
        BNE RI2
        INC $01
        DEX
        BNE RI2
        LDA #$00
        STA $00
        STA $01
        LDA #$00
        STA PSEL
        STA QH
        STA QT
        LDA #$18
        STA $2001
        RTS

TINIT:  LDA #$80
        STA $A001
        LDX #NSLOT-1
TI1:    LDA #$7F
        STA IDHI,X
        LDA #$00
        STA IDLO,X
        STA STAMP,X
        DEX
        BPL TI1
        LDA #200
        STA CLK
        LDA #$A5
        STA MAGIC
        LDA #$C0
        STA $A001
        RTS

P192LO: .db {','.join('$%02X' % ((NK1 + p * NSECOND) & 0xFF) for p in range(8))}
P192HI: .db {','.join('$%02X' % ((NK1 + p * NSECOND) >> 8) for p in range(8))}
JBLO:   .db {jl[0]}
JBHI:   .db {jl[1]}
JNLO:   .db {jl[2]}
JNHI:   .db {jl[3]}
SLOTT:  .db {','.join('$%02X' % t for t in SLOT_TILES)}
"""


def tables():
    cls = [0] * 256
    for c in range(0x40):
        cls[c] = 3
    for c in K1_CODES: cls[c] = 1
    for c in PREFIXES: cls[c] = 2
    # plain-tile batchim info in bits 4-5 (0 none,1 batchim,2 rieul,3 keep)
    for c in range(0x40, 0x100):
        if cls[c] == 0: cls[c] = 0x30
    dig = {0: 1, 1: 2, 2: 0, 3: 1, 4: 0, 5: 0, 6: 1, 7: 2, 8: 2, 9: 0}
    for d, b in dig.items():
        code = 0x5B + d if d < 5 else 0x7B + d - 5
        cls[code] = b << 4
    for i in range(26):
        L = chr(65 + i)
        cls[0x41 + i] = (2 << 4) if L in 'LR' else (1 << 4) if L in 'MN' else 0
    rank = [0] * 256
    for i, c in enumerate(K1_CODES): rank[c] = i
    return cls, rank


JOSA_TOK = ['은', '이', '을', '과', '아', '으', '이2']
JOSA_PAIR = [('은', '는'), ('이', '가'), ('을', '를'), ('과', '와'), ('아', '야'), ('으', None), ('이', None)]


def batchim(ch):
    o = ord(ch) - 0xAC00
    if o < 0 or o > 11171: return 0
    j = o % 28
    return 0 if j == 0 else (2 if j == 8 else 1)
