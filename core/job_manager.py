
import asyncio
import time
from typing import Dict, List, Optional
from core.checker_service import CheckerService

class JobStatus:
    def __init__(self, url: str):
        self.url = url
        self.status = "queued" # queued, running, completed, error
        self.total = 0
        self.current = 0
        self.message = "Waiting..."
        self.pending_logs: List[str] = []  # Queue for logs to ensure none are skipped
        self._logs_lock = asyncio.Lock()   # 保护 pending_logs 的并发访问
        self.submit_time = time.time()
        self.finish_time = None
        self.error = None

    async def update_progress(self, current: int, total: int, message: str):
        self.status = "running"
        self.current = current
        self.total = total
        self.message = message
        async with self._logs_lock:
            self.pending_logs.append(message)

    async def complete(self):
        self.status = "completed"
        self.finish_time = time.time()
        self.message = "Done"
        async with self._logs_lock:
            self.pending_logs.append("Done")

    async def get_and_clear_logs(self) -> List[str]:
        async with self._logs_lock:
            logs = self.pending_logs
            self.pending_logs = []
            return logs

    def fail(self, error: str):
        self.status = "error"
        self.error = error
        self.finish_time = time.time()
        self.message = f"Error: {error}"

class JobManager:
    def __init__(self, checker_service: CheckerService):
        self.checker = checker_service
        self.jobs: Dict[str, JobStatus] = {} # Map URL -> Status
        self.user_active_tasks: Dict[str, str] = {} # Map IP -> URL
        self.queue: asyncio.Queue = asyncio.Queue()
        self.worker_task = None
        self.running_job_url = None

    async def start_worker(self):
        if self.worker_task:
            return
        self.worker_task = asyncio.create_task(self._worker_loop())
        print("[INFO] Job Manager Worker Started", flush=True)

    async def register_completed(self, url: str):
        """Registers a job as immediately completed (for cache hits)."""
        job = JobStatus(url)
        await job.complete()  # 必须 await，因为 complete() 是 async 方法
        job.message = "Result Load from Cache"
        self.jobs[url] = job
        print(f"[INFO] Job registered as cached: {url}", flush=True)

    async def submit_job(self, url: str, file_path: str, user_ip: str = None):
        # 1. 检查该 URL 是否已有活跃任务（防止重复提交覆盖状态）
        existing = self.jobs.get(url)
        if existing and existing.status in ["queued", "running"]:
            print(f"[INFO] Job already active for {url}, skipping duplicate submit", flush=True)
            # 仍需更新 user_active_tasks 以便追踪
            if user_ip:
                self.user_active_tasks[user_ip] = url
            return  # 复用现有任务，不重复入队
        
        # 2. 用户 IP 并发检查（同一 IP 不能同时运行不同 URL 的任务）
        if user_ip:
            current_active_url = self.user_active_tasks.get(user_ip)
            if current_active_url:
                # Check status
                active_job = self.jobs.get(current_active_url)
                if active_job and active_job.status in ['queued', 'running'] and current_active_url != url:
                     # Allow re-submitting same URL (idempotent), but reject different one
                     raise ValueError(f"You already have a pending task. Please wait for it to finish.")
            
            # Update active task
            self.user_active_tasks[user_ip] = url

        # 3. Create new job status
        job = JobStatus(url)
        self.jobs[url] = job
        
        await self.queue.put((url, file_path))
        print(f"[INFO] Job submitted for {url} (User: {user_ip})", flush=True)

    def get_status(self, url: str) -> dict:
        job = self.jobs.get(url)
        # print(f"[DEBUG] get_status: '{url}' | Keys: {list(self.jobs.keys())}", flush=True)
        if not job:
            print(f"[WARN] get_status UNKNOWN: '{url}' in keys? {url in self.jobs}", flush=True)
            return {"status": "unknown"}
        
        # Calculate queue position if queued
        position = 0
        if job.status == "queued":
            # Very inefficient for large queues, but fine here
            # We assume the queue contents match the jobs marked 'queued'
            # (Simplification)
            # Actually, asyncio.Queue is opaque. 
            pass 

        return {
            "status": job.status,
            "current": job.current,
            "total": job.total,
            "message": job.message,
            "error": job.error,
            "submit_time": job.submit_time,
            "finish_time": job.finish_time
        }
    
    def is_active_task(self, url: str) -> bool:
        """Checks if a task specific to this URL is already running or queued."""
        if url in self.jobs:
            status = self.jobs[url].status
            if status in ["queued", "running"]:
                return True
        return False

    def get_queue_info(self):
        return {
            "queue_size": self.queue.qsize(),
            "running_job": self.running_job_url
        }

    async def _worker_loop(self):
        while True:
            url, file_path = await self.queue.get()
            self.running_job_url = url
            job = self.jobs[url]
            
            try:
                print(f"[INFO] Worker starting job: {url}", flush=True)
                
                async def progress_callback(current, total, msg):
                    await job.update_progress(current, total, msg)

                await self.checker.run_check(file_path, progress_cb=progress_callback)
                await job.complete()
                
            except Exception as e:
                print(f"[ERROR] Worker job failed: {e}", flush=True)
                job.fail(str(e))
            finally:
                self.running_job_url = None
                self.queue.task_done()
                
                # 清理该 URL 关联的 IP 记录，防止内存泄漏
                ips_to_clean = [ip for ip, u in self.user_active_tasks.items() if u == url]
                for ip in ips_to_clean:
                    del self.user_active_tasks[ip]
                    print(f"[INFO] Cleaned user_active_tasks for IP: {ip}", flush=True)
