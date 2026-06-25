import sys
import logging
from PyQt6.QtWidgets import QApplication

from ui import MainWindow

logger = logging.getLogger(__name__)


def main():
    """
    애플리케이션 메인 함수
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("PyScheduler")
        
        app.setStyle("Fusion")
        
        window = MainWindow()
        window.show()
        
        return app.exec()
    except Exception as e:
        logger.exception("PyScheduler failed to start: %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
