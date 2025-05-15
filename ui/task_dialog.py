from typing import List, Optional, Dict, Any, Tuple
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QComboBox,
    QTimeEdit, QSpinBox, QCheckBox, QDialogButtonBox, QGroupBox,
    QMessageBox, QRadioButton
)
from PyQt6.QtCore import Qt, QTime, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
import os

from scheduler import Task, Storage, Scheduler

class TaskDialog(QDialog):
    def __init__(self, parent: QWidget, task: Optional[Task] = None):
        super().__init__(parent)
        
        self.storage = Storage()
        self.scheduler = parent.scheduler if hasattr(parent, "scheduler") else None
        
        self.task = task
        self.is_edit_mode = task is not None
        
        self._setup_ui()
        
        if self.is_edit_mode:
            self._load_task_data()
    
    def exec(self) -> int:
        """
        대화 상자를 실행합니다. QDialog.exec()를 직접 호출합니다.
        """
        return super().exec()
        
    def _setup_ui(self) -> None:
        """
        UI 컴포넌트 설정
        """
        self.setWindowTitle("작업 추가" if not self.is_edit_mode else "작업 편집")
        self.setMinimumWidth(500)
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        
        # 작업 정보 폼
        form_layout = QFormLayout()
        
        # 작업 이름
        self.name_edit = QLineEdit()
        form_layout.addRow("작업 이름:", self.name_edit)
        
        # 실행 파일 경로
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("찾아보기...")
        self.browse_button.clicked.connect(self._on_browse_file)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        
        form_layout.addRow("실행 파일:", path_layout)
        
        # 일정 유형 선택
        self.schedule_type_combo = QComboBox()
        self.schedule_type_combo.addItems(["once", "daily", "weekly", "monthly", "interval"])
        self.schedule_type_combo.currentIndexChanged.connect(self._on_schedule_type_changed)
        
        form_layout.addRow("일정 유형:", self.schedule_type_combo)
        
        # 실행 시간
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        self.time_edit.setTime(QTime.currentTime())
        
        form_layout.addRow("실행 시간:", self.time_edit)
        
        # 주간 실행 옵션 (요일 선택)
        self.weekday_group = QGroupBox("실행 요일")
        self.weekday_group.setVisible(False)
        
        weekday_layout = QHBoxLayout()
        self.weekday_checkboxes = []
        
        weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
        for i, name in enumerate(weekday_names):
            checkbox = QCheckBox(name)
            self.weekday_checkboxes.append(checkbox)
            weekday_layout.addWidget(checkbox)
        
        self.weekday_group.setLayout(weekday_layout)
        
        # 월간 실행 옵션 (날짜 선택)
        self.monthly_group = QGroupBox("실행 날짜")
        self.monthly_group.setVisible(False)
        
        monthly_layout = QHBoxLayout()
        self.date_spinbox = QSpinBox()
        self.date_spinbox.setRange(1, 31)
        self.date_spinbox.setValue(1)
        monthly_layout.addWidget(self.date_spinbox)
        monthly_layout.addWidget(QLabel("일"))
        
        # 매월 마지막 날 실행 체크박스 추가
        self.last_day_checkbox = QCheckBox("매월 마지막 날")
        self.last_day_checkbox.toggled.connect(self._on_last_day_toggled)
        monthly_layout.addWidget(self.last_day_checkbox)
        monthly_layout.addStretch()
        
        self.monthly_group.setLayout(monthly_layout)
        
        # 주기적 실행 옵션 (시간 간격 선택)
        self.interval_group = QGroupBox("실행 주기")
        self.interval_group.setVisible(False)
        
        interval_layout = QHBoxLayout()
        
        # 사용자 지정 주기 입력
        self.interval_hours = QSpinBox()
        self.interval_hours.setRange(0, 23)
        
        self.interval_minutes = QSpinBox()
        self.interval_minutes.setRange(1, 59)
        self.interval_minutes.setValue(30)  # 기본값 30분
        
        interval_layout.addWidget(self.interval_hours)
        interval_layout.addWidget(QLabel("시간"))
        interval_layout.addWidget(self.interval_minutes)
        interval_layout.addWidget(QLabel("분"))
        interval_layout.addStretch()
        
        self.interval_group.setLayout(interval_layout)
        
        # 레이아웃 추가
        layout.addLayout(form_layout)
        layout.addWidget(self.weekday_group)
        layout.addWidget(self.monthly_group)
        layout.addWidget(self.interval_group)
        
        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def _on_browse_file(self) -> None:
        """
        실행 파일 선택 다이얼로그 표시
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "실행 파일 선택", "", "실행 파일 (*.exe);;모든 파일 (*.*)"
        )
        
        if file_path:
            self.path_edit.setText(file_path)
    
    def _on_schedule_type_changed(self, index: int) -> None:
        """
        일정 유형 변경 시 관련 UI 표시/숨김
        """
        self.weekday_group.setVisible(index == 2)  # 매주
        self.monthly_group.setVisible(index == 3)  # 매월
        self.interval_group.setVisible(index == 4)  # 주기적
        
        # 주기적 유형이 아닐 때는 시간 선택 컨트롤 활성화
        self.time_edit.setEnabled(index != 4)
    
    def _on_last_day_toggled(self, checked: bool) -> None:
        """
        매월 마지막 날 체크박스 토글 시 날짜 선택 컨트롤 활성화/비활성화
        """
        self.date_spinbox.setEnabled(not checked)
        
        # 체크박스가 선택되면 날짜를 마지막 날(31일)로 설정
        if checked:
            self.date_spinbox.setValue(31)
    
    def _load_task_data(self) -> None:
        """
        작업 데이터 로드 (편집 모드)
        """
        if not self.task:
            return
        
        self.name_edit.setText(self.task.name)
        self.path_edit.setText(self.task.file_path)
        
        # 일정 유형 설정
        schedule_type_map = {
            "once": 0,
            "daily": 1,
            "weekly": 2,
            "monthly": 3,
            "interval": 4
        }
        self.schedule_type_combo.setCurrentIndex(schedule_type_map.get(self.task.schedule_type, 0))
        
        # 실행 시간 설정
        if self.task.time:
            hours, minutes, seconds = map(int, self.task.time.split(":"))
            self.time_edit.setTime(QTime(hours, minutes, seconds))
        
        # 주간 요일 설정
        for day in self.task.days:
            if 0 <= day < len(self.weekday_checkboxes):
                self.weekday_checkboxes[day].setChecked(True)
        
        # 월간 날짜 설정
        if self.task.date:
            self.date_spinbox.setValue(self.task.date)
        
        # 매월 마지막 날 설정
        if hasattr(self.task, 'is_last_day_of_month'):
            self.last_day_checkbox.setChecked(self.task.is_last_day_of_month)
        
        # 주기적 설정 로드
        if self.task.schedule_type == "interval" and hasattr(self.task, "interval_minutes"):
            total_minutes = self.task.interval_minutes
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            self.interval_hours.setValue(hours)
            self.interval_minutes.setValue(minutes if minutes > 0 else 1)
        
        # UI 업데이트
        self._on_schedule_type_changed(self.schedule_type_combo.currentIndex())
    
    def _on_save(self) -> None:
        """
        저장 버튼 클릭 시 작업 저장
        """
        # 입력 검증
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "작업 이름을 입력하세요.")
            self.name_edit.setFocus()
            return
        
        file_path = self.path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "경고", "실행 파일을 선택하세요.")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "경고", "선택한 파일이 존재하지 않습니다.")
            return
        
        # 일정 유형 및 관련 데이터 가져오기
        schedule_type_index = self.schedule_type_combo.currentIndex()
        schedule_type_map = {
            0: "once",
            1: "daily",
            2: "weekly",
            3: "monthly",
            4: "interval"
        }
        schedule_type = schedule_type_map.get(schedule_type_index, "once")
        
        # 실행 시간
        time = self.time_edit.time().toString("HH:mm:ss")
        
        # 요일 (주간 일정)
        days = []
        if schedule_type == "weekly":
            for i, checkbox in enumerate(self.weekday_checkboxes):
                if checkbox.isChecked():
                    days.append(i)
            
            if not days:
                QMessageBox.warning(self, "경고", "하나 이상의 요일을 선택하세요.")
                return
        
        # 날짜 (월간 일정)
        date = None
        is_last_day_of_month = False
        if schedule_type == "monthly":
            is_last_day_of_month = self.last_day_checkbox.isChecked()
            date = self.date_spinbox.value()
        
        # 주기 (주기적 일정)
        interval_minutes = None
        if schedule_type == "interval":
            hours = self.interval_hours.value()
            minutes = self.interval_minutes.value()
            
            if hours == 0 and minutes == 0:
                QMessageBox.warning(self, "경고", "실행 주기를 설정하세요.")
                return
            
            interval_minutes = hours * 60 + minutes
        
        # 작업 생성 또는 업데이트
        if self.is_edit_mode and self.task:
            # 기존 작업 업데이트
            self.task.name = name
            self.task.file_path = file_path
            self.task.schedule_type = schedule_type
            self.task.time = time if schedule_type != "interval" else None
            self.task.days = days
            self.task.date = date
            self.task.is_last_day_of_month = is_last_day_of_month
            
            # 주기적 일정 속성 설정
            if schedule_type == "interval":
                self.task.interval_minutes = interval_minutes
            
            if self.scheduler:
                if self.scheduler.update_task(self.task):
                    self.accept()
                else:
                    QMessageBox.critical(self, "오류", "작업 업데이트에 실패했습니다.")
        else:
            # 새 작업 생성
            task_data = {
                "name": name,
                "file_path": file_path,
                "schedule_type": schedule_type,
                "time": time if schedule_type != "interval" else None,
                "days": days,
                "date": date,
                "is_last_day_of_month": is_last_day_of_month,
                "enabled": True
            }
            
            # 주기적 일정인 경우 interval_minutes 속성 추가
            if schedule_type == "interval":
                task_data["interval_minutes"] = interval_minutes
                
            task = Task(**task_data)
            
            if self.scheduler:
                self.scheduler.add_task(task)
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "스케줄러에 접근할 수 없습니다.") 