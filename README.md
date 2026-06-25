# PyScheduler

Windows에서 간단한 실행 파일 작업을 예약하고 관리하는 PyQt 기반 데스크톱 앱입니다.

## 기능

- 실행 파일 등록 및 스케줄 관리
- 일회성, 매일, 매주, 매월 실행 주기 지원
- 작업 활성화/비활성화
- 시스템 트레이 백그라운드 실행
- 로컬 JSON 파일 기반 작업 저장

## 기술 스택

- Python 3.12
- PyQt6
- schedule
- pydantic
- uv

## 실행

```bash
git clone https://github.com/oiloilo44/PyScheduler.git
cd PyScheduler
uv sync
uv run python main.py
```

## 테스트

현재 테스트는 GUI 대화 상자 동작을 확인하는 간단한 스모크 테스트 중심입니다.

```bash
uv run python test_dialog.py
```

## 구조

```text
scheduler/   작업 모델, 저장소, 스케줄 실행 로직
ui/          PyQt 메인 창과 작업 편집 화면
main.py      애플리케이션 진입점
```
