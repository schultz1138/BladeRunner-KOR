## 게임 「블레이드 러너 (1997)」 한국어화 패치 (ScummVM 기반)

버전: 1.0.1 (2026-03-02)  
기반: ScummVM 2026.1.0 (커스텀 빌드, Blade Runner 전용)  

Changelog 1.0.1:
- start.exe 파일 제거(바이러스 오진 방지)
- install.bat 파일 실행 시 바탕화면에 바로가기 생성
- `scummvm.exe`를 `scummvm-k.exe`로 변경 (`scummvm-k.ini` 별도 관리)

Changelog 1.0.0:
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
이 게임은 새 게임을 플레이할 때마다 사건 전개와 단서, 범인이 달라지는 구조로 되어 있어,  
정석 공략이 거의 없고 테스트 난이도가 높은 편입니다.

일반적인 게임의 인벤토리 역할을 하는 **KIA(Knowledge Integration Assistant)** 시스템은  
수사 과정에서 확보한 단서, 인물, 사건 정보를 자동으로 기록·연결하는 경찰용 정보 관리 시스템입니다.

---

## 🧪 지원되는 버전

이 패치는 **ScummVM으로 실행 가능한 원본(1997) 버전**을 기준으로 제작되었습니다.  
Nightdive Studios에서 2022년 6월 23일에 출시한 **Blade Runner: Enhanced Edition**은 지원되지 않습니다.  
하지만 GOG와 Steam에서 판매 중인 이 에디션에는 ScummVM에서 지원하는 오리지널 버전의 게임이 포함되어 있습니다.

---

## 📂 배포 리소스 구조

일반 사용자 분께서는 우측의 releases에 표시된 BladeRunner_Kor_v1.0.1_20260302.zip 파일을 다운로드 받으시거나, 아래의 주소를 직접 복사/붙여넣기 하여 BladeRunner_Kor_v1.0.1_20260302.zip 파일을 다운로드 받으시면 됩니다.

https://github.com/schultz1138/BladeRunner-KOR/releases/download/1.0.1/BladeRunner_Kor_v1.0.1_20260302.zip

파일 내부 구성은 다음과 같습니다.

```  
BladeRunner_Kor_v1.0.1_20260302.zip 기준
├─README.md
├─licenses/
├─Other_OS/
│  └─SUBTITLES.MIX
└─PC_Windows/
   ├─scummvm-k.exe
   ├─scummvm-k.ini
   ├─*.dll (15개)
   ├─RUNTIME_DLL_LIST.txt
   ├─install.bat
   ├─start.bat
   ├─config.bat
   ├─BladeRunner.ico
   └─SUBTITLES.MIX
```

---


## ✅ 설치 방법

### 방법 A: Windows PC (권장)
1) `PC_Windows` 폴더의 안에 있는 모든 파일을 **게임 폴더** 루트에 복사  
- Steam판(기본 폴더): `C:\Program Files (x86)\Steam\steamapps\common\Blade Runner Enhanced Edition\Classic`
2) `SUBTITLES.MIX` 덮어쓰기 확인이 나오면 "예" 선택
3) `install.bat` 실행 후 바탕화면에 생성된 `Blade Runner Classic (KOR)` 바로가기로 실행

### 방법 B: Android / macOS / Linux / 기존 ScummVM 사용자
1) `releases\ScummVM_Kor_Subs\Other_OS\SUBTITLES.MIX`를 게임 데이터 폴더에 복사
2) 기존 ScummVM(2.9.0 이상)으로 실행

- 이 방법은 **UI는 영문**, **자막만 한국어**로 출력됩니다.

---

## 🔤 폰트 변경 및 크기 조절 (선택)

### 폰트 변경
1) 원하는 `.ttf` 폰트를 준비
2) 파일명을 `Kor_font.ttf`로 변경
3) 게임 데이터 폴더에 넣기

`SUBTITLES.MIX`에 내장된 폰트보다 우선 적용됩니다.

### 폰트 크기 조절 (Windows 전용)
`scummvm-k.ini`에서 아래 값을 수정하세요.

- UI 폰트: `ko_font_size=9` (범위: 6 ~ 32)
- 자막 폰트: `ko_sub_font_size=20` (범위: 10 ~ 36)

예) `ko_font_size=11`, `ko_sub_font_size=22`

---

## ⚙ 기술 메모

- 리소스 로딩 우선순위: loose file -> SUBTITLES.MIX -> STARTUP.MIX
- 한국어는 SUBTITLES.MIX 내의 영문 자막 슬롯을 대체하여 표시됩니다.
- Windows 버전은 안정성과 배포 편의성을 위해 UI 리소스를 SUBTITLES.MIX에 통합했습니다.
- 설정/세이브는 `start.bat`로 실행 시 게임 폴더에 저장됩니다.
  - 설정: `scummvm-k.ini`
  - 세이브: `.\saves\`
- 커스텀 ScummVM 설정은 `config.bat`으로 접근할 수 있습니다.

---

## 📦 소스 공개 (현행 저장소 구조)

- `engine/snapshots/ScummVM_BR_2026.1.0/` : 패치 적용된 ScummVM 소스 스냅샷
- `engine/patches/` : 패치 파일 및 복사 대상 소스/빌드 설정 파일
- `engine/scripts/` : 적용/빌드/패키징/패치생성 스크립트
- `releases/ScummVM_Kor_Subs/` : 배포 리소스(자막, 배치, 설정, 라이선스, Windows 실행 파일)

통합 패치 파일:
- `engine/patches/diff/scummvm-2026.1.0_kor.patch`

---

## 🚧 알려진 사항

이 게임은 구조적으로 분기와 랜덤 시드에 의존하는 요소가 많아, 모든 상황을 완벽하게 검증하기 어렵습니다.  
따라서 일부 상황에서 번역이 어색하거나, 예상하지 못한 문제가 발생할 수 있습니다.

문제 발견 시 세이브 파일과 함께 이 저장소 Issues로 제보해 주세요.

KIA 인터페이스에서 용의자 이름이 영문으로 표시됩니다. 이름 문자열을 직접 수정할 경우  
용의자 코드가 `00-0000`으로 표기되는 버그가 있어 현재는 영문 표기를 유지합니다.

---

## 📜 라이선스

- ScummVM 엔진: GPL v3
- 나눔스퀘어B 폰트: SIL Open Font License 1.1

---

## ⚠ 주의사항

- 본 패치는 비공식 사용자 제작물입니다.
- Westwood Studios 및 ScummVM 팀은 이 프로젝트에 어떠한 책임도 없습니다.
- 게임 원본 데이터는 포함되어 있지 않습니다.
- 런타임 파일(exe/DLL) 및 커스텀 빌드 산출물은 GitHub 릴리스 업로드용으로만 사용하고 저장소에는 커밋하지 않습니다.
- **Enhanced Edition에는 적용되지 않습니다.**
- Windows에서는 반드시 `start.bat`으로 실행하세요.  
  직접 `scummvm-k.exe`를 실행하면 설정/세이브 경로가 달라질 수 있습니다.
- AI 사용 고지:
  - 초벌 번역(영어를 유럽어 자막과 비교 번역), 코드/문서 정리, 실행 파일 아이콘 제작에 AI를 사용했습니다.
  - 코드/문서의 최종 검수는 수동으로 진행했습니다.

