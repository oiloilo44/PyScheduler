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

2. 필요한 패키지를 설치합니다. (uv 패키지 매니저 사용)
```
uv init  # 이미 실행된 경우 생략
uv add PyQt6 schedule
```

3. 프로그램을 실행합니다.
```
python main.py
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
├── scheduler/           # 스케줄러 관련 모듈
│   ├── __init__.py
│   ├── models.py        # 데이터 모델
│   ├── scheduler.py     # 스케줄링 로직
│   └── storage.py       # 데이터 저장소
├── ui/                  # 사용자 인터페이스
│   ├── __init__.py
│   ├── main_window.py   # 메인 창
│   └── task_dialog.py   # 작업 추가/편집 대화상자
├── main.py              # 프로그램 진입점
└── README.md
```

## 요구 사항

- Python 3.8 이상
- PyQt6
- schedule
