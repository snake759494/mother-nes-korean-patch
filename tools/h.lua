local dir="../work/"
local L=io.open(dir.."log.txt","w")
local cmds={}
for l in io.lines(dir.."cmd.txt") do if l:match("%S") then table.insert(cmds,l) end end
local ci=1; local wait=0; local btn={}; local hold=0; local pendop=nil; local cbid=nil
local frame=0
local function doop()
  local a,b=pendop[1],pendop[2]
  if a=="save" then local s=emu.createSavestate() local h=io.open(dir..b..".mss","wb") h:write(s) h:close()
  else local h=io.open(dir..b..".mss","rb") local s=h:read("a") h:close() emu.loadSavestate(s) end
  pendop=nil
  emu.removeMemoryCallback(cbid, emu.callbackType.exec, 0x8000, 0xFFFF)
end
local function nextcmd()
  while ci<=#cmds do
    local c=cmds[ci]; ci=ci+1
    local a,b,c2=c:match("^(%S+)%s*(%S*)%s*(%S*)")
    if a=="w" then wait=tonumber(b) return
    elseif a=="p" then btn={}; for k in b:gmatch("[^,]+") do btn[k]=true end; hold=tonumber(c2) or 4; wait=hold+6 ; return
    elseif a=="shot" then local p=emu.takeScreenshot() local h=io.open(dir..b..".png","wb") h:write(p) h:close()
    elseif a=="save" or a=="load" then pendop={a,b}; cbid=emu.addMemoryCallback(doop, emu.callbackType.exec, 0x8000, 0xFFFF); wait=2; return
    elseif a=="dump" then
      local h=io.open(dir..b..".bin","wb")
      local t={}
      for i=0,0x3FFF do t[#t+1]=string.char(emu.read(i,emu.memType.nesPpuMemory)) end
      for i=0,0x7FF do t[#t+1]=string.char(emu.read(i,emu.memType.nesInternalRam)) end
      for i=0,0x1FFF do t[#t+1]=string.char(emu.read(i,emu.memType.nesSaveRam)) end
      h:write(table.concat(t)) h:close()
    elseif a=="quit" then break
    end
  end
  L:close() emu.stop(0)
end
emu.addEventCallback(function()
  frame=frame+1
  local ok,e=pcall(function() if wait>0 then wait=wait-1 if wait==0 then nextcmd() end else nextcmd() end end)
  if not ok then L:write("ERR "..tostring(e).."\n") L:close() emu.stop(1) end
end, emu.eventType.endFrame)
emu.addEventCallback(function()
  if hold>0 then hold=hold-1 local i={} for k,_ in pairs(btn) do i[k]=true end emu.setInput(i,0) end
end, emu.eventType.inputPolled)
