import json
import os
from typing import List, Dict, Any
from pathlib import Path

from scheduler.models import Task

class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.tasks_file = self.data_dir / "tasks.json"
        
        # 데이터 디렉토리가 없으면 생성
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 작업 파일이 없으면 빈 파일 생성
        if not self.tasks_file.exists():
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    def save_tasks(self, tasks: List[Task]) -> None:
        """
        작업 목록을 파일에 저장합니다.
        """
        tasks_data = [task.to_dict() for task in tasks]
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
    
    def load_tasks(self) -> List[Task]:
        """
        작업 목록을 파일에서 불러옵니다.
        """
        if not self.tasks_file.exists():
            return []
        
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            try:
                tasks_data = json.load(f)
                return [Task.from_dict(task_data) for task_data in tasks_data]
            except json.JSONDecodeError:
                # 파일이 비어있거나 잘못된 형식인 경우
                return []
            
    def add_task(self, task: Task) -> None:
        """
        새 작업을 추가합니다.
        """
        tasks = self.load_tasks()
        tasks.append(task)
        self.save_tasks(tasks)
    
    def update_task(self, task: Task) -> bool:
        """
        작업을 업데이트합니다. 성공 시 True, 실패 시 False를 반환합니다.
        """
        tasks = self.load_tasks()
        for i, t in enumerate(tasks):
            if t.id == task.id:
                tasks[i] = task
                self.save_tasks(tasks)
                return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        작업을 삭제합니다. 성공 시 True, 실패 시 False를 반환합니다.
        """
        tasks = self.load_tasks()
        initial_count = len(tasks)
        tasks = [t for t in tasks if t.id != task_id]
        
        if len(tasks) < initial_count:
            self.save_tasks(tasks)
            return True
        return False
    
    def get_task_by_id(self, task_id: str) -> Task:
        """
        ID로 작업을 찾습니다.
        """
        tasks = self.load_tasks()
        for task in tasks:
            if task.id == task_id:
                return task
        return None 