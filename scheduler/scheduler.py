import schedule
import time
import threading
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from scheduler.models import Task
from scheduler.storage import Storage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='scheduler.log'
)
logger = logging.getLogger("Scheduler")

class Scheduler:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.running = False
        self.thread = None
        self.jobs: Dict[str, schedule.Job] = {}
    
    def start(self) -> None:
        """
        스케줄러를 시작합니다.
        """
        if self.running:
            return
        
        self.running = True
        self._load_tasks()
        
        # 백그라운드 스레드에서 스케줄러 실행
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("스케줄러가 시작되었습니다.")
    
    def stop(self) -> None:
        """
        스케줄러를 중지합니다.
        """
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        logger.info("스케줄러가 중지되었습니다.")
    
    def _run_scheduler(self) -> None:
        """
        스케줄러 실행 루프
        """
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def _load_tasks(self) -> None:
        """
        저장소에서 작업을 로드하고 스케줄링합니다.
        """
        tasks = self.storage.load_tasks()
        for task in tasks:
            if task.enabled:
                self._schedule_task(task)
                # 업데이트된 다음 실행 시간을 저장소에 저장
                self.storage.update_task(task)
    
    def add_task(self, task: Task) -> None:
        """
        새 작업을 추가하고 스케줄링합니다.
        """
        self.storage.add_task(task)
        if task.enabled:
            self._schedule_task(task)
            # 업데이트된 다음 실행 시간을 저장소에 저장
            self.storage.update_task(task)
    
    def update_task(self, task: Task) -> bool:
        """
        작업을 업데이트하고 스케줄을 재조정합니다.
        """
        # 이전 작업의 스케줄 취소
        self._unschedule_task(task.id)
        
        # 작업 업데이트
        success = self.storage.update_task(task)
        
        # 업데이트된 작업 다시 스케줄링
        if success and task.enabled:
            self._schedule_task(task)
            
        return success
    
    def delete_task(self, task_id: str) -> bool:
        """
        작업을 삭제하고 스케줄을 취소합니다.
        """
        self._unschedule_task(task_id)
        return self.storage.delete_task(task_id)
    
    def toggle_task(self, task_id: str, enabled: bool) -> bool:
        """
        작업 활성화 상태를 토글합니다.
        """
        task = self.storage.get_task_by_id(task_id)
        if not task:
            return False
        
        task.enabled = enabled
        
        if enabled:
            self._schedule_task(task)
        else:
            self._unschedule_task(task_id)
            
        return self.storage.update_task(task)
    
    def _schedule_task(self, task: Task) -> None:
        """
        작업을 스케줄링합니다.
        """
        # 이미 스케줄된 작업이면 취소
        self._unschedule_task(task.id)
        
        job = None
        
        if task.schedule_type == "interval" and task.interval_minutes:
            # 주기적 실행 작업 (분 단위)
            interval_minutes = task.interval_minutes
            job = schedule.every(interval_minutes).minutes.do(self._run_task, task)
            self.jobs[task.id] = job
            
            # 다음 실행 시간 업데이트
            self._update_next_run(task)
            return
        
        # 다른 일정 유형들은 time 필드가 필요함
        if not task.time:
            logger.error(f"작업에 실행 시간이 지정되지 않았습니다: {task.name}")
            return
            
        hours, minutes, seconds = task.time.split(":")
        time_str = f"{hours.zfill(2)}:{minutes.zfill(2)}:{seconds.zfill(2)}"
        
        if task.schedule_type == "once":
            # 일회성 작업
            target_time = datetime.strptime(f"{datetime.now().date()} {time_str}", "%Y-%m-%d %H:%M:%S")
            if target_time < datetime.now():
                # 이미 지난 시간이면 다음 날로 설정
                target_time += timedelta(days=1)
            
            # 스케줄 라이브러리는 일회성 작업을 직접 지원하지 않으므로
            # 매일 실행으로 설정하고 실행 후 비활성화
            job = schedule.every().day.at(time_str).do(self._run_and_disable, task)
            
        elif task.schedule_type == "daily":
            # 매일 실행
            job = schedule.every().day.at(time_str).do(self._run_task, task)
            
        elif task.schedule_type == "weekly":
            # 매주 특정 요일에 실행
            for day in task.days:
                weekday = self._get_weekday_name(day)
                weekday_job = getattr(schedule.every(), weekday).at(time_str).do(self._run_task, task)
                self.jobs[f"{task.id}_{day}"] = weekday_job
            
        elif task.schedule_type == "monthly":
            # 매월 특정 날짜에 실행
            if task.date:
                # schedule 라이브러리는 월간 작업을 직접 지원하지 않으므로
                # 매일 검사하여 날짜가 맞으면 실행
                job = schedule.every().day.at(time_str).do(self._check_and_run_monthly, task)
        
        if job and task.schedule_type != "weekly":
            self.jobs[task.id] = job
            
        # 다음 실행 시간 업데이트
        self._update_next_run(task)
    
    def _unschedule_task(self, task_id: str) -> None:
        """
        작업의 스케줄을 취소합니다.
        """
        # 기본 작업 ID로 스케줄 취소
        if task_id in self.jobs:
            schedule.cancel_job(self.jobs[task_id])
            del self.jobs[task_id]
        
        # 주간 작업의 경우 요일별 작업 ID 확인
        for key in list(self.jobs.keys()):
            if key.startswith(f"{task_id}_"):
                schedule.cancel_job(self.jobs[key])
                del self.jobs[key]
    
    def _run_task(self, task: Task) -> None:
        """
        작업을 실행합니다.
        """
        try:
            # 하위 프로세스로 실행 파일 실행
            subprocess.Popen(task.file_path)
            
            # 마지막 실행 시간 업데이트
            task.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._update_next_run(task)
            self.storage.update_task(task)
            
            logger.info(f"작업 실행 성공: {task.name} ({task.file_path})")
        except Exception as e:
            logger.error(f"작업 실행 실패: {task.name} ({task.file_path}) - {str(e)}")
    
    def _run_and_disable(self, task: Task) -> None:
        """
        작업을 실행하고 비활성화합니다 (일회성 작업용).
        """
        self._run_task(task)
        
        # 일회성 작업은 실행 후 비활성화
        task.enabled = False
        self.storage.update_task(task)
        self._unschedule_task(task.id)
    
    def _check_and_run_monthly(self, task: Task) -> None:
        """
        월간 작업인지 확인하고 실행합니다.
        """
        today = datetime.now()
        
        if task.is_last_day_of_month:
            # 매월 마지막 날 실행 옵션이 선택된 경우
            # 현재 달의 마지막 날인지 확인
            next_month = today.month + 1 if today.month < 12 else 1
            next_month_year = today.year if today.month < 12 else today.year + 1
            last_day_of_month = (datetime(year=next_month_year, month=next_month, day=1) - timedelta(days=1)).day
            
            if today.day == last_day_of_month:
                self._run_task(task)
        # 특정 날짜가 지정된 경우
        elif today.day == task.date:
            self._run_task(task)
    
    def _update_next_run(self, task: Task) -> None:
        """
        작업의 다음 실행 시간을 업데이트합니다.
        """
        try:
            if task.schedule_type == "once" and not task.enabled:
                task.next_run = None
            else:
                # 현재 시간 기준으로 다음 실행 시간 계산
                next_run = None
                
                # 주기적 실행인 경우
                if task.schedule_type == "interval" and task.interval_minutes:
                    interval_minutes = task.interval_minutes
                    next_datetime = datetime.now() + timedelta(minutes=interval_minutes)
                    next_run = next_datetime.strftime("%Y-%m-%d %H:%M:%S")
                # 일간 실행인 경우
                elif task.schedule_type == "daily" and task.time:
                    hours, minutes, seconds = task.time.split(":")
                    next_datetime = datetime.now().replace(
                        hour=int(hours), 
                        minute=int(minutes), 
                        second=int(seconds)
                    )
                    
                    if next_datetime <= datetime.now():
                        next_datetime += timedelta(days=1)
                    
                    next_run = next_datetime.strftime("%Y-%m-%d %H:%M:%S")
                # 주간 실행인 경우
                elif task.schedule_type == "weekly" and task.time and task.days:
                    hours, minutes, seconds = task.time.split(":")
                    today = datetime.now()
                    today_weekday = today.weekday()  # 0-6 (월-일)
                    
                    # 지정된 요일 정렬 (오늘 이후로 가장 가까운 요일 찾기)
                    days_sorted = sorted(task.days)
                    
                    # 이번 주에 남은 요일 찾기
                    next_days = [day for day in days_sorted if day > today_weekday]
                    
                    if next_days:
                        # 이번 주에 실행할 요일이 남아있음
                        days_until_next = next_days[0] - today_weekday
                    else:
                        # 이번 주에 실행할 요일이 없음, 다음 주 첫 요일
                        days_until_next = 7 - today_weekday + days_sorted[0]
                    
                    next_datetime = today.replace(
                        hour=int(hours),
                        minute=int(minutes),
                        second=int(seconds)
                    ) + timedelta(days=days_until_next)
                    
                    # 오늘이고 이미 시간이 지났으면 다음 주기로
                    if days_until_next == 0 and next_datetime <= today:
                        next_days = [day for day in days_sorted if day > today_weekday + 1]
                        if next_days:
                            days_until_next = next_days[0] - today_weekday
                        else:
                            days_until_next = 7 - today_weekday + days_sorted[0]
                        next_datetime = today.replace(
                            hour=int(hours),
                            minute=int(minutes),
                            second=int(seconds)
                        ) + timedelta(days=days_until_next)
                    
                    next_run = next_datetime.strftime("%Y-%m-%d %H:%M:%S")
                
                # 월간 실행인 경우
                elif task.schedule_type == "monthly" and task.time and (task.date or task.is_last_day_of_month):
                    hours, minutes, seconds = task.time.split(":")
                    today = datetime.now()
                    
                    # 이번 달에 대한 계산
                    current_month = today.month
                    current_year = today.year
                    
                    if task.is_last_day_of_month:
                        # 매월 마지막 날 실행 옵션이 선택된 경우
                        
                        # 현재 달의 마지막 날 계산
                        next_month = current_month + 1 if current_month < 12 else 1
                        next_year = current_year if current_month < 12 else current_year + 1
                        last_day = (datetime(year=next_year, month=next_month, day=1) - timedelta(days=1)).day
                        
                        try:
                            next_datetime = today.replace(
                                day=last_day,
                                hour=int(hours),
                                minute=int(minutes),
                                second=int(seconds)
                            )
                            
                            # 이미 지난 시간이면 다음 달로 설정
                            if next_datetime <= today:
                                next_month = current_month + 1
                                next_year = current_year
                                if next_month > 12:
                                    next_month = 1
                                    next_year += 1
                                    
                                # 다음 달의 마지막 날 계산
                                month_after_next = next_month + 1 if next_month < 12 else 1
                                year_after_next = next_year if next_month < 12 else next_year + 1
                                last_day_next_month = (datetime(year=year_after_next, month=month_after_next, day=1) - timedelta(days=1)).day
                                
                                next_datetime = datetime(
                                    year=next_year,
                                    month=next_month,
                                    day=last_day_next_month,
                                    hour=int(hours),
                                    minute=int(minutes),
                                    second=int(seconds)
                                )
                        except ValueError:
                            logger.error(f"월간 작업 마지막 날 계산 오류: {task.name}")
                            next_datetime = None
                    else:
                        # 특정 날짜 선택된 경우
                        target_day = task.date
                        
                        # 현재 월부터 시작해서 12개월 전진하며 유효한 날짜 찾기
                        next_datetime = None
                        for i in range(13):  # 현재 달 포함 최대 13개월 확인 (1년 + 현재 달)
                            check_month = (current_month + i) % 12
                            check_month = 12 if check_month == 0 else check_month
                            check_year = current_year + (current_month + i - 1) // 12
                            
                            try:
                                check_date = datetime(
                                    year=check_year,
                                    month=check_month,
                                    day=target_day,
                                    hour=int(hours),
                                    minute=int(minutes),
                                    second=int(seconds)
                                )
                                
                                # 현재 시간 이후의 첫 번째 유효한 날짜 사용
                                if check_date > today or (i == 0 and check_date > today):
                                    next_datetime = check_date
                                    break
                            except ValueError:
                                # 해당 월에 그 날짜가 없으면 다음 달 확인
                                continue
                        
                        if not next_datetime:
                            logger.warning(f"유효한 월간 날짜를 찾을 수 없습니다: {target_day}일, 작업: {task.name}")
                    
                    if next_datetime:
                        next_run = next_datetime.strftime("%Y-%m-%d %H:%M:%S")
                
                task.next_run = next_run
        except Exception as e:
            logger.error(f"다음 실행 시간 업데이트 실패: {task.name} - {str(e)}")
    
    def _get_weekday_name(self, day: int) -> str:
        """
        요일 번호를 요일 이름으로 변환합니다.
        """
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if 0 <= day < len(weekday_names):
            return weekday_names[day]
        return "monday"  # 기본값 