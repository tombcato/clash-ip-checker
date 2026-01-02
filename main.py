import hashlib
import os
import time
import requests
import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from core.checker_service import CheckerService
from core.config import config
import yaml
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

app = FastAPI()

@app.get("/ipcheck")
async def root():
    return FileResponse("templates/index.html")

# Configuration
# Fix: Allow DATA_DIR override via Env to match Clash SAFE_PATHS (e.g. /root/.config/mihomo/data)
default_data_dir = os.path.join(os.getcwd(), "data")
DATA_DIR = os.getenv("DATA_DIR", default_data_dir)
os.makedirs(DATA_DIR, exist_ok=True)
print(f"LOG: Using DATA_DIR: {DATA_DIR}", flush=True)

import sys
# ... imports ...

# Global Service
from core.job_manager import JobManager

# ... imports ...

# Global Service
api_url = os.getenv("CLASH_API_URL", "http://127.0.0.1:9090")
# checker_service = CheckerService(api_url=api_url) 
# Initialized in main but logic moved
checker_service = CheckerService(api_url=api_url) 
job_manager = JobManager(checker_service)

# Force standard logging...
# ...

# Force standard logging to stdout to properly show in Docker logs
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger("Main")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Job Manager Worker...")
    await job_manager.start_worker()

def calc_md5(content) -> str:
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.md5(content).hexdigest()

def is_in_time_cache(file_path: str, max_age_seconds=None) -> bool:
    """Checks if file modification time is within max_age."""
    if max_age_seconds is None:
        max_age_seconds = config.max_age

    if not os.path.exists(file_path):
        return False
    mtime = os.path.getmtime(file_path)
    return (time.time() - mtime) < max_age_seconds

async def fetch_url_with_retry(target_url: str):
    """Helper to fetch content with specific UA."""
    headers = {"User-Agent": config.user_agent}
    print(f"[INFO] Downloading: {target_url}", flush=True)
    resp = await asyncio.to_thread(requests.get, target_url, headers=headers, timeout=config.request_timeout)
    resp.raise_for_status()
    return resp.content

def is_valid_clash(data_bytes):
    try:
        d = yaml.safe_load(data_bytes)
        return isinstance(d, dict) and 'proxies' in d
    except:
        return False

def save_file(file_path: str, content: bytes):
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}", flush=True)
        return False


@app.get("/api/status")
async def get_status_json(url: str = Query(..., description="Subscription URL")):
    """Internal JSON status API."""
    status = job_manager.get_status(url)
    q_info = job_manager.get_queue_info()
    
    # Calculate simple position info
    response = {
        "job_status": status,
        "global_queue_size": q_info["queue_size"],
        "running_job": q_info["running_job"]
    }
    
    if status["status"] == "queued":
        response["message"] = f"In Queue. Total waiting: {q_info['queue_size']}"
        
    return response

@app.get("/check")
async def ip_check(request: Request, url: str = Query(..., description="Subscription URL")): # Removed BackgroundTasks arg
    try:
        # ... fetch & validate logic (unchanged) ...
        # 1. Download Content (Initial)
        content = await fetch_url_with_retry(url)
        
        # 2. Validation & Auto-Conversion
        if not is_valid_clash(content):
             # ... auto convert logic (unchanged) ...
             # (Copy existing logic carefully or use ... if not changing)
            print("[INFO] Content is not valid Clash YAML. Attempting auto-conversion...", flush=True)
            
            try:
                # Robust URL construction using urllib
                parsed = urlparse(url)
                query = parse_qs(parsed.query)
                query.update({
                    'target': ['clash'],
                    'ver': ['meta'],
                    'flag': ['clash']
                })
                new_query = urlencode(query, doseq=True)
                new_url = urlunparse(parsed._replace(query=new_query))

                print(f"[INFO] Retrying with auto-conversion parameters...", flush=True)
                new_content = await fetch_url_with_retry(new_url)
                if is_valid_clash(new_content):
                    content = new_content
                    print(f"[INFO] Auto-conversion successful.", flush=True)
                else:
                     # ... error handling (unchanged) ...
                    msg = "Invalid Clash Configuration. Expected YAML with 'proxies' key."
                    try:
                        import base64
                        decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
                        if "vmess://" in decoded or "vless://" in decoded:
                            msg = "Received Base64/Raw Node List. Please use a 'Clash' target subscription link."
                    except:
                        pass
                    return PlainTextResponse(f"不支持的订阅类型： {msg}", status_code=400)
            except Exception as e:
                print(f"[WARN] Auto-conversion failed: {e}", flush=True)


        # 3. Calc MD5 (of valid content)
        md5_hash = calc_md5(content)
        file_name = f"{md5_hash}.yaml"
        file_path = os.path.join(DATA_DIR, file_name)

        # Update Map (URL -> Content Hash)
        url_hash = calc_md5(url)
        map_path = os.path.join(DATA_DIR, f"{url_hash}.map")
        try:
            with open(map_path, 'w') as f:
                f.write(md5_hash)
        except Exception as e:
            print(f"[WARN] Failed to save map file: {e}", flush=True)
        
        # 4. Cache Check (Now using hash of VALID content)
        exists = os.path.exists(file_path)
        in_time_cache = is_in_time_cache(file_path)
        # Check if this specific URL has a job in queue or running
        is_active = job_manager.is_active_task(url)
        
        # 5. 缓存命中：直接返回
        if exists and (in_time_cache or is_active):
            print(f"[INFO] Hit cache/reuse for {file_name} (in_time_cache={in_time_cache}, active={is_active}).", flush=True)
            if not is_active:
                await job_manager.register_completed(url)
            return FileResponse(file_path, media_type="application/x-yaml", filename="checked.yaml")
        
        # 6. 先检查队列容量（在保存文件之前）
        q_info = job_manager.get_queue_info()
        total_active = q_info["queue_size"] + (1 if q_info["running_job"] else 0)
        
        if total_active >= config.max_queue_size:
            print(f"[WARN] Queue full ({total_active} >= {config.max_queue_size}).", flush=True)
            if exists:
                # 文件已存在（可能有旧的检测结果），返回已有文件
                print(f"[INFO] Returning existing file (may contain old results).", flush=True)
                return FileResponse(file_path, media_type="application/x-yaml", filename="clash.yaml", headers={"X-QC-Queue-Full": "1"})
            else:
                # 新文件，队列满无法处理，返回 503
                return PlainTextResponse(
                    "服务器繁忙，请稍后重试。当前检测队列已满。", 
                    status_code=503,
                    headers={"X-QC-Queue-Full": "1"}
                )
        
        # 7. 队列未满，保存新文件（仅首次请求）
        if not exists:
            print(f"[INFO] New task for {file_name}.", flush=True)
            if not save_file(file_path, content):
                return PlainTextResponse("Internal Write Error", status_code=500)
        else:
            # 缓存过期，保留已有文件，直接重新检测
            print(f"[INFO] Cache stale for {file_name}, re-triggering (keeping existing file).", flush=True)

        # 8. Trigger Job with IP Limiting
        try:
             await job_manager.submit_job(url, file_path, user_ip=request.client.host)
        except ValueError as ve:
             # If user has a job running, 429 Too Many Requests
             return PlainTextResponse(str(ve), status_code=429)
        
        return FileResponse(file_path, media_type="application/x-yaml", filename="clash.yaml")

    except Exception as e:
        print(f"[ERROR] processing request: {type(e).__name__}: {e}", flush=True)
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)

@app.get("/download")
async def download_config(url: str):
    url_hash = calc_md5(url)
    map_path = os.path.join(DATA_DIR, f"{url_hash}.map")
    
    if os.path.exists(map_path):
        try:
            with open(map_path, 'r') as f:
                target_hash = f.read().strip()
            
            file_path = os.path.join(DATA_DIR, f"{target_hash}.yaml")
            if os.path.exists(file_path):
                return FileResponse(file_path, media_type="application/x-yaml", filename="clash_checked.yaml")
        except Exception as e:
            print(f"[ERROR] Map read failed: {e}", flush=True)
            pass
            
    return PlainTextResponse("File not found or expired. Please check again.", status_code=404)

@app.get("/status/stream")
async def stream_status(url: str = Query(..., description="Job URL")):
    async def event_generator():
        while True:
            # Keep alive / Heartbeat?
            if not url:
                 yield f"data: {{}}\n\n"
                 await asyncio.sleep(1)
                 continue

            status_data = job_manager.get_status(url)
            
            # Retrieve queued logs to ensure we don't miss fast updates
            job_obj = job_manager.jobs.get(url)
            logs = await job_obj.get_and_clear_logs() if job_obj else []

            if not logs:
                # No new logs, just send current state (heartbeat)
                data = json.dumps({
                    "job_status": status_data,
                    "global_queue_size": job_manager.queue.qsize()
                })
                yield f"data: {data}\n\n"
            else:
                # Send a separate event for each log message
                for msg in logs:
                    temp_status = status_data.copy()
                    temp_status["message"] = msg
                    data = json.dumps({
                        "job_status": temp_status,
                        "global_queue_size": job_manager.queue.qsize()
                    })
                    yield f"data: {data}\n\n"

            if status_data["status"] in ["completed", "error", "unknown"]:
                break

            await asyncio.sleep(1.0) # Keep 1s polling, but queue ensures no data loss

    return StreamingResponse(event_generator(), media_type="text/event-stream")

