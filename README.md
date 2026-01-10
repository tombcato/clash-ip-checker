# 🚀 Clash Node IP CHECKER

[中文](README.md) | [English](README_EN.md) | [官网](https://tombcato.github.io/clash-ip-checker/) | [Docker部署](https://github.com/tombcato/clash-ip-checker/tree/docker)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
[![Twitter](https://img.shields.io/badge/Twitter-%40hibearss-1DA1F2?style=flat&logo=twitter&logoColor=white)](https://x.com/hibearss)
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk9OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTk4IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/tombcato/clash-ip-checker)




一个针对 **Clash** (及兼容核心) 的自动化节点工具。它会自动遍历你的代理节点，通过 [IPPure](https://ippure.com/)或者[Ping0](https://ping0.cc/) 检测 IP 纯净度和相关属性，并重命名节点，添加实用的指标（IP 纯净度、Bot 比例(或共享人数)、IP属性/IP来源状态）`【🟢🟡 住宅|原生】`。
效果展示：
![图片描述](assets/clash-node-checked.png)
Web可视化配置检测：
![alt text](assets/clash-web-check.png)
## 📅 更新日志 (Changelog)

### v2.0.0 (2025-01-11)
- **Web UI**: 全新推出 Web 可视化界面，操作更便捷。
- **多源检测**: 新增 `Ping0` 检测源 支持共享人数，与 `ippure` 互补，并设为默认（速度与信息量平衡更佳）。
- **智能降级**: 新增 `Fallback` 机制，例如：Ping0 失败时自动切换至 IPPure。
- **极速默认**: 极速模式 (`fast_mode`) 默认开启，大幅提升批量检测效率。
- **单点重测**: Web 界面支持对单个节点进行重新检测，方便复核。
- **导出增强**: 支持检测结果的实时预览、编辑和一键导出，一键导入Clash
- **体验优化**: 自动清理 IP 缓存，防止结果残留；优化了端口检测和冲突处理。


## ✨ 功能特点

- **🖥️ Web 可视化界面 (新!)**: 提供现代化的 Web 界面，支持可视化配置，检测可查看实时进度显示、单点重测、结果编辑和导出预览，支持一键跳转导入Clash。
- **极速模式**: 默认 **开启**，通过 IPPure API 或者 Ping0 直接检测，速度比浏览器模式更快！可在config.yaml中设置`fast_mode = False`关闭。
- **极速模式多数据源支持**: 支持 `ping0` (默认) 和 `ippure` 两种检测源，支持自动降级 (Fallback) 机制，当 ping0 失败时自动切换到 ippure。**ippure缺少 Bot 比例分析，Ping0有共享人数数据**
- **自动切换**: 自动遍历并切换你的 Clash 代理节点。
- **深度 IP 分析**: 检测 IP 纯净度分数、Bot 比例、IP 属性 (原生/机房) 以及归属地。
- **高拟真检测 (可选)**: 在浏览器模式下使用 **Playwright** 进行高拟真检测，包含 Bot 比例分析。支持无头模式 (Headless) 配置。
- **智能过滤**: 自动跳过无效节点 (如 "到期", "流量重置", "官网" 等)。
- **配置注入**: 生成一个新的 Clash 配置文件 (`_checked.yaml`)，在节点名称后追加 Emoji 和状态信息。
- **强制全局模式**: 临时将 Clash 强制切换为全局模式以确保测试准确性。

##  ⚡新增Docker部署 [详情见Docker分支](https://github.com/tombcato/clash-ip-checker/tree/docker)
相对于主分支而言，Docker部署后代理切换不影响本地网络（部署NAS或者云服务器），且能直接输入订阅链接输出新订阅链接，没有繁琐的使用步骤，**一键替换订阅url检测！**
**云部署Demo地址：https://tombcat.space/ipcheck** 

## 🛠️ 前置要求

- **Python 3.10+**
- **Clash Verge** (或其他开启了 External Controller 的 Clash 客户端)

## 📦 安装说明

1.  **克隆仓库**
    ```bash
    git clone git@github.com:tombcato/clash-ip-checker.git
    cd clash-ip-checker
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    # 非极速模式需要
    playwright install chromium
    # 如果 install chromium 运行失败说明 playwright 没添加环境变量，可以用：
    # python -m playwright install chromium
    ```

3.  **启动 Web 界面 (新版推荐)**
    ```bash
    python web.py
    ```
    访问 http://127.0.0.1:8080 即可使用图形化界面进行配置和检测。
    
4.  **命令行模式 (旧版)**
    - 修改 `config.yaml.example` 删除后缀重命名为 `config.yaml`。
    - 编辑 `config.yaml` 填入配置（Web 界面中也可直接设置）：
        - `yaml_path`: 你的 Clash 配置文件 (**.yaml**) 的绝对路径。
        - `clash_api_secret`: 你的 API 密钥 (如果有的话)。
        - `fast_mode`: ⚡ 是否使用极速模式 (True/False)。
        - `source`: 检测源，可选 `ping0` 或 `ippure` (默认 ping0)。
        - `fallback`: 是否开启自动降级 (True/False)。
    - 运行 `python clash_automator.py`。

## Web 界面使用方法 (新版推荐)
1. 打开你的 Clash 客户端 (例如 Clash Verge) 将当前clash正在运行的订阅配置文件切换为你想要测试的订阅，点击获取YAML源代码，然后复制粘贴进[web界面](http://127.0.0.1:8080)的yaml框中
    ![alt text](assets/clash-open-yaml-code.png)
2. 确保Clash中 External Controller (外部控制) 已在设置中开启，密码随便设置, 然后再Web界面中配置
![alt text](assets/clash-controller.png)
3. 使用默认配置直接点击开始即可，检测完成后会可一键预览导入Clash
![alt text](assets/clash-web-check.png)

## 命令行模式使用方法（旧版）

1.  打开你的 Clash 客户端 (例如 Clash Verge) 将当前clash正在运行的订阅配置文件切换为你想要测试的订阅， 然后获取该配置文件的yaml文件绝对路径, 在config.yaml中配置yaml_path.
    右键配置文件选择打开文件
    ![](assets/clash-open-yaml.png)
    通过vscode获取path
    ![](assets/clash-open-yaml-vscode.png)
    或者通过记事本获取path, 鼠标悬停展示但无法复制，需要在对应的文件夹中找到再复制
    ![](assets/clash-open-yaml-jsb.png)

1.  确保 **External Controller** (外部控制) 已在设置中开启，并在config.yaml中配置clash_api_url与clash_api_secret与之对应。密码随便设置
    ![alt text](assets/clash-controller.png)
2.  运行脚本:
    ```bash
    python clash_automator.py
    ```
    *默认使用浏览器模式 (包含 Bot 检测)。如需开启 **极速模式** (速度快 10 倍，无 Bot 检测)，请在 `config.yaml` 中设置 `fast_mode = True`。*

3.  脚本将会:
    - 连接到 Clash API。
    - 切换到 "Global" (全局) 模式。
    - 逐个测试代理节点, 访问IPPure获取ip信息。
    - 生成一个名为 `your_config_checked.yaml` 的新文件。
4.  在项目当前文件夹下将生成的 `_checked.yaml` 文件导入 Clash 即可切换该配置查看结果！
    导入_checked.yaml配置
    ![](assets/clash-import.png)

## 📝 输出示例

你的代理节点将会被重命名，直观展示其质量：

### 🔍 结果解读

格式： `【🟢🟡 机房|广播】` (默认浏览器模式) 或 `【⚪ 机房|广播】` (极速模式)

*   **第 1 个 Emoji (⚪)**: **IP 纯净度** (值越低越好，越低越像真实用户)
*   **第 2 个 Emoji (🟡)**: **Bot 比例** (浏览器模式独有，值越高来自机器人的流量更大更容易弹验证)
*   **属性**: 住宅 / 机房 
*   **来源**: 原生 / 广播

#### 📊 评分对照表

| 范围 | Emoji | 含义 |
| :--- | :---: | :--- |
| **0 - 10%** | ⚪ | **极佳** |
| **11 - 30%** | 🟢 | **优秀** |
| **31 - 50%** | 🟡 | **良好** |
| **51 - 70%** | 🟠 | **中等** |
| **71 - 90%** | 🔴 | **差** |
| **> 90%** | ⚫ | **极差** |

#### 🏷️ 常见标签说明

*   **住宅 (Residential)**: 家庭宽带 IP，隐蔽性高，被封锁概率低。
*   **机房 (Datacenter)**: 数据中心 IP，速度快但容易被识别。
*   **原生 (Native)**: 指该 IP 归属于当地运营商，通常解锁流媒体 (Netflix, Disney+) 效果最好。
*   **广播 (Broadcast)**: IP 地理位置与注册地不符。

## ⚙️ 配置项

查看 `config.yaml.example` 获取所有可用配置项的说明。

## 🤝 贡献参与

欢迎提交 Pull Request 来改进这个项目！

## ⚠️ 免责声明

本工具仅供教育和测试使用。请遵守当地法律法规，并合理使用代理服务。

## 🌟 Star 记录

[![Star History Chart](https://api.star-history.com/svg?repos=tombcato/clash-ip-checker&type=Date)](https://star-history.com/#tombcato/clash-ip-checker&Date)






