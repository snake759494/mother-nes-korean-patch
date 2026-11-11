local W={}
emu.addMemoryCallback(function(a,v) W[a]=true end, emu.callbackType.write, 0x0000, 0x7FFF)
local n=0
emu.addEventCallback(function() n=n+1
  if n==tonumber(os.getenv("NF") or "6000") then
    local f=io.open("../work/wcov.txt","w")
    for a=0,0x7fff do if W[a] then f:write(string.format("%04x\n",a)) end end
    f:close() emu.stop(0) end
end, emu.eventType.endFrame)
-- simple input: mash a/start pattern
emu.addEventCallback(function()
  local k=n%240
  local i={}
  if n<3000 then if k<5 then i.start=true elseif k>=120 and k<125 then i.a=true end
  else local d=math.floor(n/180)%4; if d==0 then i.left=true elseif d==1 then i.down=true elseif d==2 then i.right=true else i.up=true end if k<4 then i.a=true end if k>=60 and k<64 then i.b=true end end
  emu.setInput(i,0)
end, emu.eventType.inputPolled)
