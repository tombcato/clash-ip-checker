# Clash IP Checker - 任务状态流程图

## 任务生命周期状态图

```mermaid
stateDiagram-v2
    [*] --> Idle: 初始状态

    Idle --> Requesting: 用户点击"开始检测"
    note right of Requesting
        生成新的 request_id
        清空日志
        禁用开始按钮
    end note

    Requesting --> CacheCheck: 后端收到 /check 请求
    
    state CacheCheck <<choice>>
    CacheCheck --> CacheHit: 文件存在 & 未过期 & 非取消 & 非新请求
    CacheCheck --> NewTask: 否则
    
    CacheHit --> Completed: 返回缓存文件
    
    NewTask --> Queued: 提交到 JobManager
    note right of Queued
        如果存在旧任务:
        调用 old_job.cancel()
        覆盖 self.jobs[url]
    end note
    
    Queued --> Running: Worker 取出任务开始执行
    
    Running --> Checking: 遍历每个节点
    Checking --> Checking: 检测下一个节点
    Checking --> Completed: 所有节点检测完成
    Checking --> Cancelled: stop_event.is_set()
    
    Running --> Error: 发生异常
    
    state StopButton {
        [*] --> StopClicked: 用户点击"停止"
        StopClicked --> CancelCheck: 发送 /cancel?request_id=xxx
        
        state CancelCheck <<choice>>
        CancelCheck --> CancelSuccess: request_id 匹配当前任务
        CancelCheck --> CancelIgnored: request_id 不匹配 (旧请求)
        
        CancelSuccess --> Cancelled: 设置 stop_event
    }
    
    Cancelled --> Idle: 用户点击"检测其他"
    Completed --> Idle: 用户点击"检测其他"
    Error --> Idle: 用户点击"重试"
```

## 缓存决策流程图

```mermaid
flowchart TD
    A["收到 /check 请求"] --> B{"文件存在?"}
    B -->|否| C["下载订阅内容"]
    B -->|是| D{"max_age 内?"}
    
    D -->|是| E{"is_active?"}
    D -->|否| F{"is_cancelled?"}
    
    E -->|是| G{"request_id 相同?"}
    E -->|否| F
    
    G -->|是| H["返回缓存 (复用进行中任务)"]
    G -->|否| I["绕过缓存, 取消旧任务, 启动新任务"]
    
    F -->|是| I
    F -->|否| H
    
    C --> J["保存文件"]
    J --> K["提交新任务到队列"]
    I --> K
    
    K --> L["返回文件响应"]
```

## request_id 机制说明

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端 (index.html)
    participant B as 后端 (/check)
    participant J as JobManager
    participant W as Worker
    
    U->>F: 点击 "开始检测"
    F->>F: 生成 request_id = UUID
    F->>F: localStorage.set('active_task_id', UUID)
    F->>B: GET /check?url=...&request_id=UUID
    
    B->>J: submit_job(url, request_id)
    
    alt 存在旧任务 (不同的 request_id)
        J->>J: old_job.cancel()
        J->>W: stop_event.set() (通知 Worker 停止)
    end
    
    J->>J: 创建新 JobStatus(request_id)
    J->>J: queue.put(task)
    B-->>F: FileResponse
    
    W->>W: 从队列取出任务
    W->>W: 检测节点...
    
    U->>F: 点击 "停止"
    F->>F: 取出 localStorage['active_task_id']
    F->>B: POST /cancel?request_id=UUID
    B->>J: cancel_job(url, request_id)
    
    alt request_id 匹配
        J->>J: job.cancel()
        J->>W: stop_event.set()
        W->>W: 检测到 stop_event, 中断循环
    else request_id 不匹配
        J-->>B: 忽略 (返回 not_found_or_ignored)
    end
```

## JobStatus 状态定义

| 状态 | 描述 | 触发条件 |
|-----|------|---------|
| `queued` | 任务已提交，等待 Worker 处理 | `submit_job()` 创建 |
| `running` | Worker 正在执行检测 | `update_progress()` 调用 |
| `completed` | 所有节点检测完成 | `complete()` 调用 |
| `cancelled` | 用户主动取消 | `cancel()` 调用 |
| `error` | 检测过程发生异常 | `fail()` 调用 |

## 关键设计决策

1. **request_id 隔离**: 每次点击"开始检测"生成唯一 UUID，确保取消操作只影响对应的任务
2. **旧任务自动取消**: 当新请求覆盖旧任务时，先调用 `cancel()` 通知 Worker 停止
3. **缓存绕过**: 即使缓存有效，如果 `request_id` 不同，也会启动新任务
4. **日志清理**: 前端在开始新任务时清空旧日志，避免混淆
