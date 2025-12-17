# 部署到 Google Cloud Platform (GCP) 指南

本项目基于 Docker 构建，支持部署到 Google Cloud 的多种服务。推荐使用 **Cloud Run** (Serverless, 按需付费) 或 **Compute Engine** (VM, 类似传统服务器)。



## Compute Engine (GCE)

如果你需要**持久化缓存**，或者希望通过 Docker Compose 管理，可以使用 VM。

### 1. 创建 VM 实例

在 GCP 控制台创建一个实例（推荐 "Container Optimized OS" 或 Ubuntu）。
*   机器类型: `e2-micro` (免费层级) 或 `e2-small` 即可。
*   防火墙: 勾选 "Allow HTTP traffic"，并在网络设置中放行 8000 端口。

### 2. 部署

SSH 登录到 VM，然后拉取代码并运行：

```bash
# 安装 Docker & Git (如果使用 Ubuntu)
sudo apt-get update && sudo apt-get install -y docker.io docker-compose git

# 克隆代码
git clone https://github.com/tombcato/clash-ip-checker.git
cd clash-ip-checker
# 2. 切换Docker分支
git checkout docker

# 运行
sudo docker-compose up -d --build
```

### 3. 配置防火墙规则 (重要)

您截图中的界面是正确的 ("VPC firewall rules")。默认情况下 GCP 只开放 80/443/22 端口，您需要手动开放 8000 端口。

1.  在 GCP 控制台点击顶部 **"Create firewall rule"** (或“创建防火墙规则”)。
2.  填写如下信息：
    *   **Name (名称)**: `allow-clash-8000`
    *   **Targets (目标)**: 选择 `All instances in the network` (网络中的所有实例)。
    *   **Source filter (来源过滤)**: `IPv4 ranges`
    *   **Source IPv4 ranges (来源 IP 范围)**: `0.0.0.0/0` (允许所有 IP 访问)。
    *   **Protocols and ports (协议和端口)**:
        *   勾选 `TCP`
        *   在输入框填入 `8000`
3.  点击 **Create**。

等待几秒后，防火墙规则生效，您就可以通过 `http://[External_IP]:8000/ipcheck` 访问了。

---

## 常见问题

### 端口配置
我们在 `entrypoint.sh` 中配置了 `uvicorn ... --port ${PORT:-8000}`。Cloud Run 会自动注入 `PORT` 环境变量（通常是 8080），应用会自动适配。

### 内存不足
如果遇到 Clash 启动失败或检测过程中崩溃，请尝试增加内存限制（GCE 升级机型或 Cloud Run 增加 `--memory 2Gi`）。
