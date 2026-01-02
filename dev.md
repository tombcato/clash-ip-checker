# 新功能：集成 Subconverter 订阅转换

## 概述
将当前针对非 Clash 订阅的临时 URL 参数拼接处理逻辑，替换为集成 `subconverter` 服务。这将显著提高对各种订阅格式（如 Base64, V2Ray, SSR 等）的兼容性。
同时，利用 Subconverter 的能力，支持 **多平台输出**，允许用户将检测后的高质量节点直接导出为 Surge, QuantumultX, Loon 等格式。

## 方案分析与风险评估

### 优势 (Pros)
1.  **极佳的兼容性**: Subconverter 是业界标准的转换工具，支持 V2Ray, SSR, Trojan, Base64 等几乎所有主流格式，解决了仅靠拼接 `target=clash` 无法处理很多原生格式的问题。
2.  **解耦与稳定性**: 将复杂的解析逻辑剥离给专用服务，减少了主程序的维护负担。
3.  **标准化输出**: 确保生成的 YAML 是标准的 Clash Meta 格式，减少因格式错误导致的 Clash 启动失败。

### 劣势 (Cons) -> *可接受*
1.  **部署复杂度**: 需要额外运行一个 docker 容器 (虽然 docker-compose 可以一键编排，但增加了系统资源占用)。
2.  **依赖性**: 主程序现在强依赖 subconverter 服务，如果该服务挂掉，转换功能将不可用。

### 边缘情况与潜在风险 (Edge Cases)
1.  **服务不可达**: 若 container 未启动或配置错误，请求会超时。
    *   *对策*: 在 `main.py` 中增加 `try-except` 和超时设置 (e.g. 10秒)，并返回清晰的报错 "转换服务不可用"。
2.  **特殊网络环境 (Loopback/Intranet)**:
    *   Docker 容器内的 `localhost` 和宿主机的 `localhost` 不同。
    *   *对策*: 默认配置必须区分 Docker 环境 (`http://subconverter:25500`) 和 本地开发环境 (`http://127.0.0.1:25500`)。
3.  **URL 编码问题**:
    *   传递给 Subconverter 的 `url` 参数必须进行正确的 URL Encode，否则包含特殊字符 (`&`, `?`) 的订阅链接会被截断。
    *   *对策*: 使用 `urllib.parse.quote` 处理原始链接。
4.  **超大订阅源**:
    *   某些机场订阅包含数千个节点，转换可能会超时。
    *   *对策*: 适当放宽 http client 的 timeout 时间。
5.  **隐私问题**:
    *   虽然是本地搭建，但仍需确保 subconverter 镜像来源可靠 (`tindy2013/subconverter` 是官方受信任版本)。

## 涉及模块变更

### 1. 配置 (`core/config.py`)
- **变更**: 新增配置项 `SUBCONVERTER_URL`。
- **原因**: 用于定义 subconverter 服务的地址。
- **默认值 (本地)**: `http://127.0.0.1:25500` (用户本地运行或 host 模式)。
- **默认值 (Docker)**: `http://subconverter:25500` (引用 docker-compose 中的服务名)。
- **公共服务备选 (不推荐隐私数据使用)**:
    - `https://api.v1.mk/sub?` (肥羊增强版)
    - `https://sub.xeton.dev/sub?`
    - `https://api.tsutsu.one/sub?`
    - `https://sub.d1.mk/sub?`
    > **注意**: 使用公共转换服务意味着你的订阅链接（包含节点信息）会被发送到第三方服务器。建议仅在测试或确信服务安全时使用。本方案默认推荐使用 Docker 本地自建服务。

- **配置项**: `SUBCONVERTER_REMOTE_CONFIG` (新增)
- **原因**: 允许用户自定义生成的 YAML 中的分流规则和策略组 (如 ACL4SSR)。
- **默认值**: 空字符串 (使用 Subconverter 默认规则)。
- **默认值**: 空字符串 (使用 Subconverter 默认规则)。
- **常用示例**: `https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/config/ACL4SSR_Online_Mini.ini` (该规则将作用于最终导出的订阅，自动生成策略组)

### 2. 主程序逻辑 (`main.py`)
- **位置**: `ip_check` 函数，位于 `if not is_valid_clash(content):` 判断块内。
- **变更**:
    - **移除**: 原有的 `urlparse` 解析及 `target=clash`, `ver=meta` 参数硬编码拼接逻辑。
    - **新增**: 构建请求到配置的 `SUBCONVERTER_URL` 的逻辑。
        - URL构造: `{SUBCONVERTER_URL}/sub?target=clash&url={Encoded_URL}&insert=false`
        - **优化**: 如果配置了 `SUBCONVERTER_REMOTE_CONFIG`，追加 `&config={Encoded_Config_URL}` 参数。
    - **新增**: 清晰的错误捕获，区分 "原链接无法下载" 和 "转换失败"。
    - **新增**: **多平台输出逻辑**
        - `/check` 接口增加 `target` 参数 (默认为 `clash`)。
        - **支持格式**:
            - **通用/标准** (推荐): `mixed` (Base64混合), `clash`, `clashr`, `ss`, `ssr`, `v2ray`
            - **iOS/Mac**: `surge` (Ver 4), `quanx` (Quantumult X), `loon`
            - **Android**: `surfboard`
        - 流程：
            1. 输入订阅 -> 转 Clash -> 测速 -> 得到 `checked.yaml` (Clash格式)。
                - 参数 `config`: 使用 `SUBCONVERTER_REMOTE_CONFIG` (如 ACL4SSR) 来生成分流规则。
            3. **清洗 (Clean)**: (暂不启用) 既然用户希望保留标签信息，我们可以跳过此步骤，保留 `[NF]` 等标签，以便用户直观看到解锁情况。
            4. 返回最终结果。

### 3. 基础设施 (`docker-compose.yml`)
- **变更**: 新增 `subconverter` 容器服务。
- **镜像**: `tindy2013/subconverter:latest`
- **端口**: 内部使用，映射 `25500:25500` (可选，便于调试)。
- **重启策略**: `always`。

## 执行计划
1. 修改 `docker-compose.yml` 加入 subconverter 服务。
2. 更新 `core/config.py` 读取环境变量。
3. 重构 `main.py` 对接转换逻辑。

## 资源优化 (Optional)
**问**: 如果我配置了外部的 `SUBCONVERTER_URL`，是否还需要启动本地的 subconverter 容器？
**答**: 不需要。虽然默认提供的 `docker-compose.yml` 会包含该服务以确保“开箱即用”和隐私安全，但如果您指定了外部服务，可以在 `docker-compose.yml` 中注释掉或删除 `subconverter` 服务块，以节省系统资源。
