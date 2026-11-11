# MOTHER (패미컴) 비공식 한글패치

패미컴 일본판 **MOTHER (마더, 1989)** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `Mother (Japan).nes`** (No-Intro 형식, iNES 헤더 포함)를 준비합니다.
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\Mother (Japan).nes'`
2. xdeltaUI 같은 도구로 원본 `.nes` 에 `Mother_KO_v1.0.xdelta` 를 적용합니다. (Patch = xdelta, Source File = 원본 ROM, Output File = 새 파일명)
   - 명령줄: `xdelta3 -d -s "Mother (Japan).nes" Mother_KO_v1.0.xdelta "Mother (Korean).nes"`
3. 만들어진 `.nes` 를 Mesen 등 **매퍼 191(NES 2.0)을 지원하는** 에뮬레이터에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 ROM 크기 | 393,232 바이트 |
| 원본 ROM CRC32 | `cb084ac5` |
| 원본 ROM MD5 | `bf1e0bc9c390fdbb2b3ca22d784db7d2` |
| 원본 ROM SHA-256 | `ac14a63c080d810adcc1f43c102fcab8740425bd7404050216790aedc396ee2b` |
| xdelta SHA-256 | `12b70298a60d492b97686f85212571ed12bec98ddb9f74de8aea41cd362f98c9` |
| 결과 ROM 크기 | 655,376 바이트 |
| 결과 ROM SHA-256 | `1ff266b76455a77289228a94b0765f2a7e66ee45deb82a1a82cdd33ea24f3874` |

## 주의
- 원본에서 만든 **상태저장(세이브 스테이트)** 과 세이브 파일(.sav)은 쓰지 마세요. ROM 구조가 달라 글자가 깨지거나 멈출 수 있습니다. 새로 시작해 주세요.
- 패치 후 ROM은 PRG 512KB·매퍼 191(MMC3 + CHR-RAM)입니다. 실기·플래시 카트리지에서는 동작을 확인하지 않았습니다.
- xdelta는 압축하지 않은 형식(`-0`)입니다(약 50KB).

## 한글화 내용
- 본편 대사 904개, 전투 메시지, 아이템·PSI·상태 이름, 적 이름, 메뉴, 프롤로그, 이름 입력 화면 전수 직접 번역
- 한글 849자: 자주 쓰는 155자는 1바이트, 나머지는 2바이트 부호. 글자는 그릴 때마다 CHR-RAM 캐시에 올림
- 이름 뒤 조사(은/는·이/가·을/를 등)를 받침에 맞게 자동 선택
- 이름 입력 표를 한글 음절로 교체
- 글꼴: 갈무리7(8×8 원래 크기, 확대·축소 없음)

## 그대로 둔 것
- 타이틀 로고 「MOTHER」 등 영문 표기, 음악

## 검증 범위
Mesen에서 타이틀·파일 선택·이름 입력·프롤로그·필드 대화·메뉴·상태 화면·아이템·전투(조사·승리 메시지 포함)를 직접 확인했습니다. 본편 대사 894개를 Lua 스크립트로 실제 대사 창에 하나씩 띄워 화면 글자를 글리프와 대조해 깨진 글자가 없는 것을 확인했습니다. 전체 플레이 검증은 하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — ROM 구조와 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
