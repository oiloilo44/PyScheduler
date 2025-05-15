from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import uuid

ScheduleType = Literal["once", "daily", "weekly", "monthly", "interval"]

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    file_path: str
    schedule_type: ScheduleType
    time: Optional[str] = None  # HH:MM:SS 형식, interval 타입에서는 None 가능
    days: List[int] = []  # 주간 실행 시 요일 (0-6, 월-일)
    date: Optional[int] = None  # 월간 실행 시 날짜 (1-31)
    is_last_day_of_month: bool = False  # 매월 마지막 날 실행 여부
    enabled: bool = True
    last_run: Optional[str] = None  # 마지막 실행 시간
    next_run: Optional[str] = None  # 다음 실행 예정 시간
    interval_minutes: Optional[int] = None  # 주기적 실행 시 분 단위 간격

    def update_next_run(self) -> None:
        """
        다음 실행 시간을 업데이트합니다.
        """
        # 추후 구현
        pass

    def to_dict(self) -> dict:
        """
        Task를 사전 형태로 변환합니다.
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """
        사전 형태에서 Task 객체를 생성합니다.
        """
        return cls(**data) 