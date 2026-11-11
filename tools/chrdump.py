import sys
from PIL import Image
d=open('../Mother (Japan).nes','rb').read()
chr_=d[16+0x40000:]
n=len(chr_)//16
cols=32
rows=(n+cols-1)//cols
im=Image.new('P',(cols*8,rows*8))
im.putpalette([0,0,0,255,255,255,128,128,128,200,80,80]+[0]*756)
px=im.load()
for t in range(n):
    b=chr_[t*16:t*16+16]
    for y in range(8):
        for x in range(8):
            v=((b[y]>>(7-x))&1)|(((b[y+8]>>(7-x))&1)<<1)
            px[(t%cols)*8+x,(t//cols)*8+y]=v
im=im.resize((im.width*2,im.height*2))
# split into parts of 1KB (64 tiles = 2 rows)
h=im.height
for i in range(0,h,512):
    im.crop((0,i,im.width,min(h,i+512))).save('chr_%02d.png'%(i//512))
