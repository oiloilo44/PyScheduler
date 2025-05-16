import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QMenu, QSystemTrayIcon, QCheckBox,
    QLabel, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QAction

from scheduler import Task, Storage, Scheduler

# TaskDialog를 직접 import하지 않고, 필요할 때 동적으로 가져오기
def get_task_dialog(parent, task=None):
    from ui.task_dialog import TaskDialog
    return TaskDialog(parent, task)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 저장소 및 스케줄러 초기화
        self.storage = Storage()
        self.scheduler = Scheduler(self.storage)
        
        self._setup_ui()
        self._load_tasks()
        
        # 작업 목록 타이머 (10초마다 업데이트)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._load_tasks)
        self.update_timer.start(10000)
        
        # 카운트다운 타이머 (1초마다 업데이트)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_timer.start(1000)
        self.countdown_seconds = 10  # 남은 시간 초기화
        
        # 스케줄러 시작
        self.scheduler.start()
        
    def _setup_ui(self) -> None:
        """
        UI 컴포넌트 설정
        """
        self.setWindowTitle("PyScheduler")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 작업 추가 버튼
        self.add_button = QPushButton("작업 추가")
        self.add_button.clicked.connect(self._on_add_task)
        button_layout.addWidget(self.add_button)
        
        # 작업 편집 버튼
        self.edit_button = QPushButton("작업 편집")
        self.edit_button.clicked.connect(self._on_edit_task)
        button_layout.addWidget(self.edit_button)
        
        # 작업 삭제 버튼
        self.delete_button = QPushButton("작업 삭제")
        self.delete_button.clicked.connect(self._on_delete_task)
        button_layout.addWidget(self.delete_button)
        
        # 레이아웃에 버튼 추가
        main_layout.addLayout(button_layout)
        
        # 작업 테이블
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(["이름", "경로", "일정 유형", "실행 시간", "다음 실행", "활성화"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 테이블 더블 클릭 이벤트
        self.task_table.cellDoubleClicked.connect(self._on_table_double_clicked)
        
        main_layout.addWidget(self.task_table)
        
        # 남은 시간 표시 레이아웃
        countdown_layout = QHBoxLayout()
        countdown_layout.addStretch()
        
        # 남은 시간 레이블
        self.countdown_label = QLabel("목록 새로고침까지 10초 남음")
        countdown_layout.addWidget(self.countdown_label)
        countdown_layout.addStretch()
        
        main_layout.addLayout(countdown_layout)
        
        # 시스템 트레이 아이콘 설정
        self._setup_system_tray()
    
    def _setup_system_tray(self) -> None:
        """
        시스템 트레이 아이콘 설정
        """
        # 시스템 트레이 아이콘 메뉴
        tray_menu = QMenu()
        
        # 열기 액션
        show_action = QAction("열기", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        # 종료 액션
        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self._on_exit)
        tray_menu.addAction(quit_action)
        
        # 시스템 트레이 아이콘 설정
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("PyScheduler")
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        
        # 아이콘이 없으면 간단히 시스템 기본 아이콘 사용
        self.tray_icon.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_ComputerIcon))
        self.tray_icon.show()
    
    def _update_countdown(self) -> None:
        """
        남은 시간 카운트다운 업데이트
        """
        self.countdown_seconds -= 1
        if self.countdown_seconds <= 0:
            self.countdown_seconds = 10
            
        self.countdown_label.setText(f"목록 새로고침까지 {self.countdown_seconds}초 남음")
    
    def _load_tasks(self) -> None:
        """
        저장소에서 작업 목록을 로드하고 테이블에 표시
        """
        # 카운트다운 초기화
        self.countdown_seconds = 10
        self.countdown_label.setText(f"목록 새로고침까지 {self.countdown_seconds}초 남음")
        
        # 현재 선택된 작업 ID 저장
        selected_task_id = self._get_selected_task_id()
        
        tasks = self.storage.load_tasks()
        self.task_table.setRowCount(0)  # 테이블 초기화
        
        task_id_to_row = {}  # 작업 ID와 행 번호 매핑
        
        for i, task in enumerate(tasks):
            self.task_table.insertRow(i)
            
            # 이름
            self.task_table.setItem(i, 0, QTableWidgetItem(task.name))
            
            # 경로
            self.task_table.setItem(i, 1, QTableWidgetItem(task.file_path))
            
            # 일정 유형
            self.task_table.setItem(i, 2, QTableWidgetItem(task.schedule_type))
            
            # 실행 시간
            time_info = task.time if task.time else ""
            if task.schedule_type == "weekly" and task.days:
                weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
                weekdays = [weekday_names[day] for day in task.days]
                time_info += f" ({', '.join(weekdays)})"
            elif task.schedule_type == "monthly":
                if hasattr(task, 'is_last_day_of_month') and task.is_last_day_of_month:
                    time_info += " (매월 마지막 날)"
                elif task.date:
                    time_info += f" ({task.date}일)"
            elif task.schedule_type == "interval" and task.interval_minutes:
                hours = task.interval_minutes // 60
                minutes = task.interval_minutes % 60
                
                if hours > 0:
                    time_info = f"{hours}시간 "
                time_info += f"{minutes}분마다"
            
            self.task_table.setItem(i, 3, QTableWidgetItem(time_info))
            
            # 다음 실행
            next_run = task.next_run if task.next_run else "없음"
            self.task_table.setItem(i, 4, QTableWidgetItem(next_run))
            
            # 활성화 체크박스 (셀 안에 넣기)
            checkbox = QCheckBox()
            checkbox.setChecked(task.enabled)
            # 명시적인 함수를 사용하여 체크박스 상태 변경 연결
            checkbox.stateChanged.connect(self._create_checkbox_handler(task.id))
            
            # 체크박스를 셀 중앙에 배치
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(layout)
            
            self.task_table.setCellWidget(i, 5, cell_widget)
            
            # 작업 ID 저장 (숨겨진 데이터)
            item = self.task_table.item(i, 0)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, task.id)
                task_id_to_row[task.id] = i  # 작업 ID와 행 번호 매핑
        
        # 이전에 선택된 작업이 있으면 다시 선택
        if selected_task_id and selected_task_id in task_id_to_row:
            row_to_select = task_id_to_row[selected_task_id]
            self.task_table.selectRow(row_to_select)
    
    def _get_selected_task_id(self) -> Optional[str]:
        """
        선택된 작업의 ID를 반환
        """
        selected_rows = self.task_table.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        item = self.task_table.item(row, 0)
        if not item:
            return None
            
        return item.data(Qt.ItemDataRole.UserRole)
    
    def _on_add_task(self) -> None:
        """
        작업 추가 다이얼로그 표시
        """
        dialog = get_task_dialog(self)
        if dialog.exec():
            self._load_tasks()
    
    def _on_edit_task(self) -> None:
        """
        선택된 작업 편집
        """
        task_id = self._get_selected_task_id()
        if not task_id:
            QMessageBox.warning(self, "경고", "편집할 작업을 선택하세요.")
            return
            
        task = self.storage.get_task_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "경고", "작업을 찾을 수 없습니다.")
            return
            
        dialog = get_task_dialog(self, task)
        if dialog.exec():
            self._load_tasks()
    
    def _on_delete_task(self) -> None:
        """
        선택된 작업 삭제
        """
        task_id = self._get_selected_task_id()
        if not task_id:
            QMessageBox.warning(self, "경고", "삭제할 작업을 선택하세요.")
            return
            
        reply = QMessageBox.question(
            self, "작업 삭제", "선택한 작업을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.scheduler.delete_task(task_id):
                self._load_tasks()
            else:
                QMessageBox.warning(self, "오류", "작업 삭제에 실패했습니다.")
    
    def _create_checkbox_handler(self, task_id: str):
        """
        체크박스 상태 변경 이벤트 핸들러를 생성
        """
        def handler(state: int):
            is_checked = state == Qt.CheckState.Checked.value
            self._on_toggle_task(task_id, is_checked)
        return handler
    
    def _on_toggle_task(self, task_id: str, enabled: bool) -> None:
        """
        작업 활성화 상태 변경
        """
        success = self.scheduler.toggle_task(task_id, enabled)
        if not success:
            QMessageBox.warning(self, "오류", "작업 상태 변경에 실패했습니다.")
            # 상태 변경 실패 시 테이블 다시 로드
            self._load_tasks()
    
    def _on_table_double_clicked(self, row: int, column: int) -> None:
        """
        테이블 더블 클릭 이벤트 처리
        """
        self._on_edit_task()
    
    def _on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        시스템 트레이 아이콘 활성화 이벤트 처리
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # 우클릭 이벤트 발생 시 아무 작업도 수행하지 않음
            # 컨텍스트 메뉴는 자동으로 표시됨
            pass
    
    def _on_exit(self) -> None:
        """
        프로그램 종료
        """
        self.scheduler.stop()
        QApplication.quit()
    
    def closeEvent(self, event):
        """
        창 닫기 이벤트 처리 - 시스템 트레이로 최소화
        """
        event.ignore()
        self.hide()
        
        # 처음 닫을 때만 메시지 표시
        if not hasattr(self, "_first_close_shown"):
            self.tray_icon.showMessage(
                "윈도우 작업 스케줄러",
                "프로그램이 계속 실행 중입니다. 아이콘을 더블 클릭하여 다시 열 수 있습니다.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
            self._first_close_shown = True


class TaskDialog(QWidget):
    """
    작업 추가/편집 다이얼로그
    """
    # 실제 구현은 여기에 추가됩니다.
    pass 