from typing import Dict, Callable, Optional
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self, config: Dict):
        """
        初始化调度器。
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.morning = config.get('morning', {'hour': 8, 'minute': 0})
        self.evening = config.get('evening', {'hour': 18, 'minute': 0})
        self._jobs = []
        self._running = False
    
    def add_job(self, func: Callable, trigger: str, **kwargs) -> None:
        """
        添加任务。
        
        Args:
            func: 任务函数
            trigger: 触发方式 (morning/evening/interval)
            **kwargs: 其他参数
        """
        job = {
            'func': func,
            'trigger': trigger,
            'kwargs': kwargs
        }
        self._jobs.append(job)
        logger.info(f"添加任务: {func.__name__}, 触发方式: {trigger}")
    
    def _run_job(self, job: Dict, report_type: str) -> None:
        """
        执行任务。
        
        Args:
            job: 任务配置
            report_type: 报告类型
        """
        func = job['func']
        kwargs = job.get('kwargs', {})
        
        try:
            logger.info(f"开始执行任务: {func.__name__}")
            func(report_type=report_type, **kwargs)
            logger.info(f"任务执行完成: {func.__name__}")
        except Exception as e:
            logger.error(f"任务执行失败: {func.__name__}, 错误: {e}")
    
    def run_morning(self) -> None:
        """运行早报任务"""
        logger.info("执行早报任务")
        for job in self._jobs:
            if job['trigger'] in ['morning', 'both']:
                self._run_job(job, '早报')
    
    def run_evening(self) -> None:
        """运行晚报任务"""
        logger.info("执行晚报任务")
        for job in self._jobs:
            if job['trigger'] in ['evening', 'both']:
                self._run_job(job, '晚报')
    
    def start(self) -> None:
        """启动调度器"""
        if not self.enabled:
            logger.info("调度器未启用")
            return
        
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            scheduler = BackgroundScheduler()
            
            # 早报任务
            morning_trigger = CronTrigger(
                hour=self.morning.get('hour', 8),
                minute=self.morning.get('minute', 0)
            )
            scheduler.add_job(self.run_morning, morning_trigger)
            logger.info(f"早报任务已调度: {self.morning.get('hour', 8):02d}:{self.morning.get('minute', 0):02d}")
            
            # 晚报任务
            evening_trigger = CronTrigger(
                hour=self.evening.get('hour', 18),
                minute=self.evening.get('minute', 0)
            )
            scheduler.add_job(self.run_evening, evening_trigger)
            logger.info(f"晚报任务已调度: {self.evening.get('hour', 18):02d}:{self.evening.get('minute', 0):02d}")
            
            scheduler.start()
            self._running = True
            logger.info("调度器已启动")
            
            # 保持运行
            try:
                import time
                while self._running:
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                self.stop()
                
        except ImportError:
            logger.warning("apscheduler未安装，使用简单调度")
            logger.info("请运行: pip install apscheduler")
            self._simple_schedule()
    
    def _simple_schedule(self) -> None:
        """简单的调度方式（无依赖）"""
        import time
        
        logger.info("使用简单调度模式")
        
        # 计算下次执行时间
        def get_next_run(hour: int, minute: int) -> float:
            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                # 如果目标时间已过，计算明天的
                from datetime import timedelta
                target += timedelta(days=1)
            return (target - now).total_seconds()
        
        while self._running:
            # 计算距离下次早报和晚报的时间
            morning_seconds = get_next_run(
                self.morning.get('hour', 8),
                self.morning.get('minute', 0)
            )
            evening_seconds = get_next_run(
                self.evening.get('hour', 18),
                self.evening.get('minute', 0)
            )
            
            # 选择最近的任务执行
            if morning_seconds < evening_seconds:
                wait_seconds = morning_seconds
                next_task = 'morning'
            else:
                wait_seconds = evening_seconds
                next_task = 'evening'
            
            logger.info(f"下次任务: {next_task}, 等待 {wait_seconds/3600:.1f} 小时")
            
            # 等待（每小时检查一次）
            wait_hours = int(wait_seconds // 3600)
            for _ in range(wait_hours):
                time.sleep(3600)
                if not self._running:
                    break
            
            # 执行任务
            if self._running:
                if next_task == 'morning':
                    self.run_morning()
                else:
                    self.run_evening()
    
    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        logger.info("调度器已停止")
    
    def run_once(self, report_type: str = "早报") -> None:
        """
        立即执行一次任务。
        
        Args:
            report_type: 报告类型
        """
        if report_type == "早报":
            self.run_morning()
        else:
            self.run_evening()
