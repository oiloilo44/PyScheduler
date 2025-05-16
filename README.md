# PyScheduler - 윈도우 작업 스케줄러

PyScheduler는 Windows 작업 스케줄러와 유사한 기능을 제공하는 Python 기반 애플리케이션입니다. 사용자가 실행 파일(.exe)을 등록하고 정해진 일정에 따라 자동으로 실행되도록 스케줄을 설정할 수 있습니다.

## 주요 기능

- .exe 파일 추가 및 관리
- 다양한 실행 주기 설정 (일회성, 매일, 매주, 매월)
- 요일 및 날짜 선택 기능
- 시스템 트레이에서 백그라운드 실행
- 프로그램 종료 후에도 스케줄 유지

## 설치 방법

1. 저장소를 클론합니다.
```
git clone https://github.com/yourusername/pyscheduler.git
cd pyscheduler
```

2. 패키지 설치 및 환경 동기화
(이미 pyproject.toml과 uv.lock이 있으므로 아래 명령만 실행)
```
uv sync
```

- 추가 패키지가 필요하면:  
  `uv add <패키지명>`

3. 프로그램 실행
```
uv run main.py
```

## 사용 방법

1. "작업 추가" 버튼을 클릭하여 새 작업을 추가합니다.
2. 작업 이름을 입력하고 실행할 .exe 파일을 선택합니다.
3. 실행 주기와 시간을 설정합니다.
4. "저장" 버튼을 클릭하여 작업을 추가합니다.
5. 작업 목록에서 작업의 활성화 상태를 토글할 수 있습니다.
6. 메인 창을 닫으면 프로그램은 시스템 트레이에서 계속 실행됩니다.

## 프로젝트 구조

```
pyscheduler/
├── data/                # 작업 데이터 저장 디렉토리
│   └── tasks.json       # 작업 설정 저장 파일
├── main.py              # 프로그램 진입점
├── main.dist/           # 빌드 결과물(배포용)
├── main.build/          # 빌드 중간 산출물
├── scheduler/           # 스케줄러 관련 모듈
│   ├── __init__.py
│   ├── models.py        # 데이터 모델
│   ├── scheduler.py     # 스케줄링 로직
│   └── storage.py       # 데이터 저장소
├── ui/                  # 사용자 인터페이스
│   ├── __init__.py
│   ├── main_window.py   # 메인 창
│   └── task_dialog.py   # 작업 추가/편집 대화상자
├── .venv/               # 가상환경(uv)
├── .gitignore           # Git 무시 파일
├── pyproject.toml       # 프로젝트 설정 및 의존성
├── uv.lock              # 의존성 잠금 파일(반드시 버전 관리)
├── .python-version      # Python 버전 지정
└── README.md
```

## 요구 사항

- Python 3.12 이상
- PyQt6
- schedule
- pydantic
- nuitka (빌드용)
- uv (패키지 매니저)

## 기타 참고 사항

- `.venv/`는 반드시 .gitignore에 포함하세요.
- `pyproject.toml`, `uv.lock`는 반드시 버전 관리에 포함하세요.
- 데이터 파일(`data/`), 빌드 산출물(`main.dist/`, `main.build/`), 로그(`*.log`, `scheduler.log`) 등은 .gitignore에 포함되어야 합니다.
