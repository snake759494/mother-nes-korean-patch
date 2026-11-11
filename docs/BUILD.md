# 빌드 방법

번역 대본(`tools/tr/`)과 글꼴 파일은 저장소에 없으므로, 아래는 같은 자료를 갖춘 경우의 절차입니다. 모든 명령은 `tools/` 폴더에서 실행합니다.

## 준비
- Python 3.11 이상, `pip install pillow`
- 원본 `Mother (Japan).nes` (README의 해시와 일치)를 저장소 최상위 폴더에 둡니다.
- 글꼴: `tools/dl/gal/Galmuri7.ttf`

## 순서
1. 원문 추출: `charset.decode()`로 PRG `0x30000-0x37EF6`의 대사를 읽어 `tr/main_0.json`~`tr/main_7.json`(`[{"id","jp"}]`), 전투·아이템·적 이름은 `tr/misc_jp.json`
2. 번역: `tr/ko_0.json`~`tr/ko_7.json`(`[{"id","ko"}]`), `tr/misc_ko.json` — 형식 규칙(한 줄 18칸, `{STR}`·`{NUM}` 토큰 유지, 조사 토큰 `{은}` `{이}` `{을}` 등)
3. 빌드: `python make.py "../Mother (Japan) [한글패치].nes"`
4. 검증: `python vfy.py` (ROM에 들어간 대사를 번역문과 바이트 단위로 대조)
5. 차분 파일: `xdelta3 -e -0 -S none -s "Mother (Japan).nes" "Mother (Japan) [한글패치].nes" Mother_KO_v1.0.xdelta`

## 에뮬레이터 시험
`run.sh`가 Mesen 테스트러너로 `h.lua`를 실행합니다. `cmd.txt`에 `w 프레임`, `p 버튼 [유지]`, `shot 이름`, `save/load 이름`, `dump 이름`, `quit` 명령을 한 줄씩 적습니다.
