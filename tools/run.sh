#!/bin/bash
# usage: run.sh rom
cd /d/nes/마더/emu && rm -f Saves/*.sav; timeout ${TO:-300} ./Mesen.exe --testrunner "$(cygpath -w "$1")" "$(cygpath -w /d/nes/마더/work/${HL:-h.lua})" 2>&1 | grep -v Uninit > /dev/null
