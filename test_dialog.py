import sys
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QLabel

class TestDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("테스트 대화 상자")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("이것은 테스트 대화 상자입니다."))
        btn = QPushButton("확인")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

def main():
    app = QApplication(sys.argv)
    dialog = TestDialog()
    
    result = dialog.exec()  # 여기서 exec() 메서드를 호출
    print(f"대화 상자 결과: {result}")
    
if __name__ == "__main__":
    main() 