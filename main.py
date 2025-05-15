import sys
import traceback
from PyQt6.QtWidgets import QApplication

from ui import MainWindow

def main():
    """
    애플리케이션 메인 함수
    """
    try:
        print("애플리케이션 시작...")
        app = QApplication(sys.argv)
        app.setApplicationName("PyScheduler")
        
        # 스타일 설정 (선택 사항)
        print("스타일 설정...")
        app.setStyle("Fusion")
        
        # 메인 윈도우 생성 및 표시
        print("메인 윈도우 생성...")
        window = MainWindow()
        print("메인 윈도우 표시...")
        window.show()
        
        # 애플리케이션 실행
        print("애플리케이션 실행...")
        return app.exec()
    except Exception as e:
        print(f"오류 발생: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
