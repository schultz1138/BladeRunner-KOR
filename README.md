## 게임 「블레이드 러너 (1997)」 한국어화 패치 (ScummVM 기반)

버전: 1.0 (2026-02-08)  
기반: ScummVM 2026.1.0 (커스텀 빌드, Blade Runner 전용)  

Changelog:
- 컷신/인게임 자막 한국어화  
- Windows용 KIA/UI 한글 표시 지원  
- 폰트 교체 및 크기 조절 옵션 추가  

이 패치는 1997년작 어드벤처 게임 **Blade Runner**의 한국어 번역을 제공합니다.  
> ScummVM 기반 **Blade Runner (1997)** 한국어 번역 패치입니다.  
> Windows에서는 **한글 UI + 음성 자막**, 기타 OS에서는 **자막**만 지원합니다. 

---

## 🎮 게임 소개

**Blade Runner (1997)** 는 Westwood Studios가 제작한 포인트 앤 클릭 어드벤처입니다.  
1982년 영화와 같은 세계관이지만, 영화의 내용을 그대로 옮긴 게임은 아닙니다.  
(데커드 역의 해리슨 포드는 여기에서 직접적으로 등장하지 않습니다. 하지만 숀 영은 레이첼 역으로 등장합니다.)

플레이어는 1982년 영화와 동일한 시간대에서, 형사 레이 맥코이가 되어 레플리컨트를 추적합니다.  
이 게임은 새 게임을 플레이할 때마다 사건 전개와 단서, 범인이 달라지는 구조로 되어있어,  
정석 공략이 거의 없고 테스트 난이도가 높은 편입니다.  
(...네. 이건 디버깅이 쉽지 않았고, 번역 검수와 오탈자 수정이 쉽지않았다는 핑계입니다.)

일반적인 게임의 인벤토리 역할을 하는 **KIA(Knowledge Integration Assistant)** 시스템은  
수사 과정에서 확보한 단서, 인물, 사건 정보를 자동으로 기록·연결하는 경찰용 정보 관리 시스템 입니다.

게임 진행에서 필수적인 부분이니 만큼, 아래 설치방법 에서 '방법 A: Windows PC' 방식의 설치를 권해드립니다. 

---

## 🧪 지원되는 버전

이 패치는 **ScummVM으로 실행 가능한 원본(1997) 버전**을 기준으로 제작되었습니다.  
Nightdive Studios에서 2022년 6월 23일에 출시한 **Blade Runner: Enhanced Edition**은 지원되지 않습니다.  
하지만 GOG와 Steam에서 판매중인 이 에디션에는 ScummVM에서 지원하는 오리지널 버전의 게임이 포함되어 있습니다.  

---

## 📌 패치 개요

- 컷신 및 인게임 음성 자막 한국어화
- Windows 환경에서 한글 UI(옵션 및 KIA 시스템) 지원
- 커스텀 ScummVM 기반 동작
  - Blade Runner 엔진만 포함한 경량 빌드
  - UTF-8 기반 UI 한글 문자열 처리 및 출력

---

## 📂 배포 구성 (사용자용 zip)

BladeRunner_Kor_v1.0.zip  
│  COPYING.txt          - ScummVM 라이선스 안내  
│  FONT_LICENSE.txt   - 나눔스퀘어 폰트 라이선스  
│  ReadMe.txt            - 사용 방법 안내  
│  
├─Other_OS  
│  └─SUBTITLES.MIX       - macOS/Android/Linux 등 타 OS용 한국어 자막  
│  
└─PC_Windows  
   ├─scummvm.exe          - 커스텀 ScummVM (2026.1.0 기반, Blade Runner 전용)  
   ├─scummvm.ini           - 커스텀 설정 파일  
   ├─*.dll (15개)              - 커스텀 ScummVM 실행용 라이브러리 DLL  
   ├─start.exe                 - 게임 실행 (아이콘 적용됨)  
   ├─start.bat                 - 게임 실행 (백신 오진/실행 불가 시 사용)  
   ├─config.exe               - 설정 실행 (아이콘 적용됨)  
   ├─config.bat               - 설정 실행 (백신 오진/실행 불가 시 사용)  
   └─SUBTITLES.MIX         - Windows용 자막 + UI 통합 파일  

---

## ✅ 설치 방법

### 방법 A: Windows PC (권장)
1) PC_Windows 폴더의 모든 파일을 **게임 폴더**에 복사
2) `start.exe` 실행

### 방법 B: Android / macOS / Linux / 기존 ScummVM 사용자
1) Other_OS 폴더의 `SUBTITLES.MIX`를 **게임 데이터 폴더**에 복사
2) 기존 ScummVM(2.9.0 이상)으로 실행

- 이 방법은 **UI는 영문**, **자막만 한국어**로 출력됩니다.

---

## 🔤 폰트 변경 및 크기 조절 (선택)

### 폰트 변경
1) 원하는 `.ttf` 폰트를 준비
2) 파일명을 `Kor_font.ttf`로 변경
3) 게임 데이터 폴더에 넣기

SUBTITLES.MIX에 내장된 폰트보다 **우선 적용**됩니다.

### 폰트 크기 조절 (Windows 전용)
`scummvm.ini`에서 아래 값을 수정하세요.

- UI 폰트: `ko_font_size=9` (범위: 6 ~ 32)
- 자막 폰트: `ko_sub_font_size=20` (범위: 10 ~ 36)

예) `ko_font_size=11`, `ko_sub_font_size=22`

---

## ⚙ 기술 메모

- 리소스 로딩 우선순위: loose file → SUBTITLES.MIX → STARTUP.MIX
- 한국어는 SUBTITLES.MIX 내의 **영문 자막 슬롯**을 대체하여 표시됩니다.
- Windows 버전은 안정성과 배포 편의성을 위해 **UI 리소스를 SUBTITLES.MIX에 통합**
- 설정/세이브는 **start.exe로 실행 시** 게임 폴더에 저장되도록 구성되었습니다.
  - 설정: `scummvm.ini`
  - 세이브: `.\Saved Games\`
- 커스텀 scummvm의 설정은 `config.exe`를 실행해서 접근할 수 있습니다.  
  해당 설정에서는 아래의 이스터에그들과 치트를 설정할 수 있습니다.
  - 시트콤 모드
  - 쇼티 모드
  - 프레임 제한 고성능 모드
  - 초당 최대 프레임 제한
  - 맥코이의 빠른 스테미나 감소를 비활성화
  - 텍스트 크롤링 중 자막 표시 (기본으로 활성화)
* `start.exe`와 `config.exe` 파일은 bat 파일을 exe로 변환한 파일입니다.  
  백신 문제로 exe 실행이 되지않는 경우, `start.bat` 과 `config.bat` 으로 실행하실 수 있습니다.

---

## 📜 라이선스

- ScummVM 엔진: **GPL v3**
- 나눔스퀘어B 폰트: **SIL Open Font License 1.1**

---

## 📦 소스 공개

이 패치의 소스는 다음 구조로 공개됩니다.

- `ScummVM_2026.1.0\` : ScummVM 2026.1.0 전체 소스 (패치 적용본)
- `Patch_2026.1.0\`	: 수정된 소스 파일만 모은 패치 세트 + diff
- `Release_Kor_Subs_v1.0` : 커스텀 빌드를 제외한 배포 패키지 (UI 스트링 및 자막, 설정파일, 실행용 배치파일)

diff 파일:
- `Patch_2026.1.0\diff\scummvm-2026.1.0_kor.patch`

---

## 🚧 알려진 사항
이 게임은 구조적으로 분기와 랜덤 시드에 의존하는 요소가 많아, 모든 상황을 완벽하게 검증하기 어렵습니다.  
따라서 일부 상황에서 번역이 어색하거나, 예상하지 못한 문제가 발생할 수 있습니다.  

문제 발견 시 Saved Games에 저장된 세이브 파일과 함께 제보해 주시면 큰 도움이 됩니다.

KIA 인터페이스에서 용의자 이름이 영문으로 표시됩니다.  
이름에 해당하는 Actors를 수정할 경우, 용의자 코드가 00-0000 으로 표기되는 버그가 있어, 현재는 영문을 표기하는 방법을 선택하였습니다. 

---

## 🙏 감사

본 패치는 ScummVM 팀의 Blade Runner Subtitles Add-on 파일을 기반으로 만들어졌습니다. 
- ScummVM 팀의 모든 개발자분들
- Michael Liebscher (Blade Runner 리버스 엔지니어링 및 FON 파일 포맷 분석)
- Ben Damer (br-mixer 제작 및 리소스 파일 포맷 분석)

또한, Blade Runner 한국어화를 위해 오랜 시간 도전과 시도를 이어온 분들께 감사드립니다.
- nsm53pr 님
- darkx 님
- 추리소년(故 박주항) 님 (덕분에 많은 게임을 한국어로 즐길 수 있었습니다. 감사합니다.)

---

## ⚠ 주의사항

- 본 패치는 비공식 사용자 제작물입니다.
- Westwood Studios 및 ScummVM 팀과는 무관합니다.
- 게임 원본 데이터는 포함되어 있지 않습니다.
- Enhanced Edition에는 적용되지 않습니다.
- Windows에서는 반드시 `start.exe`로 실행해야 합니다.  
  직접 scummvm.exe 실행 시 설정/세이브 경로가 달라질 수 있습니다.
- AI 사용 고지:  
	- 초벌 번역 (영어를 프랑스어, 독일어, 이탈리아어 번역과 비교 번역)과 코드/문서 정리, 실행 파일의 아이콘 제작에 AI를 사용했습니다.  
	- 코드/문서의 최종 검수는 수동으로 진행했습니다. 단, 일부 미검수된 부분이 남아있을 수 있습니다.

