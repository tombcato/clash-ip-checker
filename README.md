# 🚀 Clash Node IP CHECKER

[中文](README.md) | [English](README_EN.md)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

一个针对 **Clash Verge** (及兼容核心) 的智能自动化工具。它会自动遍历你的代理节点，通过 [IPPure](https://ippure.com/) 检测 IP 纯净度和风险值，并重命名节点，添加实用的指标（IP 纯净度、Bot 比例、IP属性/IP来源状态）`【🟢🟡 住宅|原生】`。

![图片描述](assets/clash-node-checked.png)

> **注意**: 本工具使用 **Playwright** 进行高拟真的浏览器指纹检测，确保检测结果与真实用户体验一致。

## ✨ 功能特点

- **自动切换**: 自动遍历并切换你的 Clash 代理节点。
- **深度 IP 分析**: 检测 IP 纯净度分数、Bot 比例、IP 属性 (原生/机房) 以及归属地。
- **智能过滤**: 自动跳过无效节点 (如 "到期", "流量重置", "官网" 等)。
- **配置注入**: 生成一个新的 Clash 配置文件 (`_checked.yaml`)，在节点名称后追加 Emoji 和状态信息。
- **强制全局模式**: 临时将 Clash 强制切换为全局模式以确保测试准确性。

## 🛠️ 前置要求

- **Python 3.10+**
- **Clash Verge** (或其他开启了 External Controller 的 Clash 客户端)
- **Playwright** (用于浏览器自动化)

## 📦 安装说明

1.  **克隆仓库**
    ```bash
    git clone git@github.com:tombcato/clash-ip-checker.git
    cd clash-ip-checker
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    #如果install chromium运行失败说明playwright没添加环境变量 可以用 python -m playwright install chromium
    ```

3.  **配置文件**
    - 修改 `config.yaml.example` **删除文件名.example 重命名为 `config.yaml`** 重要！！！。
    - 编辑 `config.yaml` 填入你的信息（具体见下面使用方法）：
        - `yaml_path`: 你的 Clash 配置文件 (**.yaml**) 的绝对路径。
        - `clash_api_secret`: 你的 API 密钥 (如果有的话)。

## 🚀 使用方法

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
3.  脚本将会:
    - 连接到 Clash API。
    - 切换到 "Global" (全局) 模式。
    - 逐个测试代理节点, 访问ippure获取ip信息。
    - 生成一个名为 `your_config_checked.yaml` 的新文件。
4.  在项目当前文件夹下将生成的 `_checked.yaml` 文件导入 Clash 即可切换该配置查看结果！
    导入_checked.yaml配置
    ![](assets/clash-import.png)

## 📝 输出示例

你的代理节点将会被重命名，直观展示其质量：

### 🔍 结果解读

格式： `【🟢🟡 属性|来源】`

*   **第 1 个 Emoji (🟢)**: **IP 纯净度** (值越低越好，越低越像真实用户)
*   **第 2 个 Emoji (🟡)**: **Bot 比例** (值越低越不容易被反爬，越高来自机器人的流量更大更容易弹验证)
*   **属性**: 机房、住宅 
*   **来源**: 原生、广播

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

*   **原生 (Native)**: 指该 IP 归属于当地运营商，通常解锁流媒体 (Netflix, Disney+) 效果最好。
*   **机房 / 数据中心**: 托管在云服务商的 IP，速度快但可能被流媒体封锁。
*   **广播**: IP 地理位置与注册地不符。

## ⚙️ 配置项

查看 `config.yaml.example` 获取所有可用配置项的说明。

### 🚀 性能优化选项

在 `config.yaml` 中可以配置以下选项来加快测试速度：

| 配置项 | 默认值 | 说明 |
| :--- | :---: | :--- |
| `fast_mode` | `true` | 启用快速模式，使用 API 直接查询 IP 信息，跳过浏览器检测 |
| `switch_delay` | `0.5` | 切换代理后的等待时间（秒）|
| `retry_delay` | `1` | 检测失败后重试前的等待时间（秒）|

**配置示例：**
```yaml
# 性能选项 (可选)
fast_mode: true      # 快速模式 - 大幅提升速度
switch_delay: 0.5    # 代理切换延迟 (秒)
retry_delay: 1       # 重试延迟 (秒)
```

> **💡 提示**: 启用 `fast_mode` 后，每个节点的测试时间可以从 5-10 秒缩短到 1-2 秒。

## 🤝 贡献参与

欢迎提交 Pull Request 来改进这个项目！

## ⚠️ 免责声明

本工具仅供教育和测试使用。请遵守当地法律法规，并合理使用代理服务。
