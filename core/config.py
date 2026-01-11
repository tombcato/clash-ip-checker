import os
import yaml
import logging

# Defaults
DEFAULT_CONFIG = {
    "api_url": "http://127.0.0.1:9090",
    "check_url": "https://my.123169.xyz/v1/info",
    "request_timeout": 10,
    "mixed_port": 7890,
    "user_agent": "ClashVerge/2.4.3 Mihomo/1.19.17",
    "skip_keywords": ["剩余", "到期", "有效期", "重置", "官网", "网址", "更新", "公告", "建议"],
    "max_age": 3600, # 秒，缓存最大时间 超过这个时间会重新检查ip否则用缓存
    "max_queue_size": 10, # 最大任务队列数
}

class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        # Allow overriding config path
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    # Deep merge not strictly needed for this flat structure but good practice?
                    # For now just update keys
                    self._config.update(user_config)
                    print(f"LOG: Loaded config from {config_path}", flush=True)
            except Exception as e:
                 print(f"LOG: Failed to load config: {e}. Using defaults.", flush=True)
        else:
             print(f"LOG: Config file {config_path} not found. Using defaults.", flush=True)

    def get(self, key, default=None):
        return self._config.get(key, default)

    @property
    def api_url(self): return self._config["api_url"]
    
    @property
    def check_url(self): return self._config["check_url"]
    
    @property
    def request_timeout(self): return self._config["request_timeout"]
    
    @property
    def user_agent(self): return self._config["user_agent"]

    @property
    def max_queue_size(self): return self._config.get("max_queue_size", 10)
    
    @property
    def skip_keywords(self): return self._config["skip_keywords"]
    
    @property
    def max_age(self): return self._config["max_age"]

    @property
    def mixed_port(self): return self._config["mixed_port"]

    @property
    def source(self): return self._config.get("source", "ping0")

    @property
    def fallback(self): return self._config.get("fallback", True)

# Singleton instance
config = Config()
