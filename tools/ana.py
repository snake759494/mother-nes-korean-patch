import sys
d=open(sys.argv[1],'rb').read()
ppu=d[:0x4000]; ram=d[0x4000:]
rom=open('../Mother (Japan).nes','rb').read()
chr_=rom[16+0x40000:]
for k in range(8):
    blk=ppu[k*0x400:(k+1)*0x400]
    idx=[i for i in range(128) if chr_[i*0x400:(i+1)*0x400]==blk]
    print('ppu %04x: chr1k banks'%(k*0x400),idx)
import os; nt=ppu[int(os.environ.get("NT","2000"),16):][:0x3c0]
for r in range(30):
    print('%2d '%r+' '.join('%02x'%b for b in nt[r*32:r*32+32]))
