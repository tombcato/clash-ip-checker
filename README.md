# ⚡ Clash IP Checker 👉 [Docker Demo](https://tombcat.space/ipcheck)

一个基于 **Clash Meta (Mihomo)** 和 **FastAPI** 的高性能 IP 风险检测工具，
专为筛选高质量节点设计，提供 API 订阅转换服务 和 Web 可视化面板。

> **功能亮点**: 相对于[main分支](https://github.com/tombcato/clash-ip-checker/tree/main)而言，Docker版部署后代理切换不占用影响本地网络，且能直接输入订阅链接输出新订阅链接，没有繁琐的使用步骤，正真做到一键替换

---

## 核心功能

*   **API 订阅转换**: 可直接拼成带检测结果的订阅链接替换原始订阅， 可多次刷新该链接，IP检测结果会通过该链接增量更新
    *   👉 **订阅格式**:   
    本地docker服务： `http://127.0.0.1:8000/check?url=[原始订阅链接]`  
    云服务器： `http://[服务器IP]:8000/check?url=[原始订阅链接]`
*   **Web 可视化面板**: 现代化的 Vue/Tailwind 界面，可视化配置，实时显示检测进度和日志。
    *   👉 **访问地址**:   
        本地docker服务：`http://127.0.0.1:8000/ipcheck`  
        云服务器：`http://[服务器IP]:8000/ipcheck`
*   **智能缓存系统**:
    *   基于内容 MD5 的去重缓存 (默认10分支有效期)。
    *   **任务复用**: 多个用户同时请求相同订阅时，共享同一个检测任务
*   **数据源可选**: `Ping0` 和 `ippure`, 可选降级策略

![alt text](assets/docker-home.png)

## 🆕 v1.1.0 新增功能 （2026-01-11）

*   **Web页面UI优化**: 新增高级设置，可视化配置，支持随时中断正在进行的检测任务
*   **数据源可选**: 新增`Ping0`数据源，检测结果显示 IP 被多少设备共享
*   **数据源策略**: 可选降级，例如优选`Ping0` 失败后自动切换到`ippure`
*   **Mihomo内核更新**: 更新至v1.19.18
*   **自动解包**: 自动识别并处理嵌套的检测链接 (`/check?url=...`)
*   **竞态防护**: Request ID 机制防止取消操作影响新任务
*   **状态流程图**: 新增 [`docs/job_state_diagram.md`](./docs/job_state_diagram.md)

> 完整变更日志请查看 [CHANGELOG.md](./CHANGELOG.md)
---
## ⚠️ 关于本地 Docker 部署(仅作Demo演示，建议NAS/云服务器部署)

原因如下：
1. **本地网络干扰**: 本地可能存在防火墙、路由器 NAT、ISP 干扰等因素，导致部分节点无法正常连接或检测超时。

2. **资源占用**: Clash 需要切换大量节点并发起 HTTP 请求，会占用本地网络带宽和系统资源。

3. **推荐方案**: 
   - 使用NAS 局域网部署 
   - 使用云服务器部署（如 GCP、AWS、阿里云等）

---

## 🚀 快速开始

### 使用 Docker Compose 

最简单的部署方式。只需一条命令：

```bash
# 1. 克隆代码
git clone https://github.com/tombcato/clash-ip-checker.git
cd clash-ip-checker

# 2. 切换Docker分支
git checkout docker

# 3. 启动服务
docker-compose up -d --build
```

启动后，访问 **[http://127.0.0.1:8000/ipcheck](http://127.0.0.1:8000/ipcheck)** 即可使用。  
我自己云部署的Demo【仅测试】: https://tombcat.space/ipcheck
![alt text](assets/docker-home.png)

也可以直接在Clash中添加替换的订阅链接 `http://127.0.0.1:8000/check?url=[原始订阅链接]`, 添加后通过刷新订阅看到检测结果，订阅不多的话一般一分钟可以完全检测完成，未完成的话可以继续刷新，直到检测完成，也可前往 http://127.0.0.1:8000/ipcheck 查看进度
![alt text](assets/docker-clash-config.png)




如要部署到Google Cloud (GCP)详见部署指南：[📄 DEPLOY_GCP.md](./DEPLOY_GCP.md)

---



## 🛠️ 配置说明

可通过修改 `config.yaml` 或环境变量调整行为：

| 配置项 | 环境变量 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `max_queue_size` | `MAX_QUEUE_SIZE` | `10` | 最大并发检测任务数 |
| `max_age` | `MAX_AGE` | `360` | 缓存有效期 (秒)，`0` 表示不缓存 |
| `request_timeout` | `REQUEST_TIMEOUT` | `10` | 每个节点检测的超时时间 (秒) |
| `source` | `SOURCE` | `ping0` | 优先数据源 (`ping0` / `ippure`) |
| `fallback` | `FALLBACK` | `true` | 主源失败时是否尝试备用源 |
| `skip_keywords` | - | 见下方 | 包含这些关键词的节点将被跳过 |

**默认跳过关键词**: `剩余`, `重置`, `到期`, `有效期`, `官网`, `网址`, `更新`, `公告`, `建议`

> 💡 **提示**: 前端"高级设置"面板可以覆盖上述配置（仅对当前请求生效）


---

## 🔒 隐私与免责

*   **数据隐私**: 本工具仅作为网络连接性测试用途
*   **免责申明**: 本项目按“现状”提供，开发者不对因使用本工具导致的任何后果（如流量消耗、账号封禁等）负责。请务必遵守当地法律法规。

