<div align="center">
  <img src="resources/icons/WinMsgHub_ICON.png" alt="WinMsgHub Logo" width="128" height="128">
  <h1>WinMsgHub</h1>
  <h3>一站式消息接收 · 多源聚合 · 智能通知</h3>

  <p>
    <img src="https://img.shields.io/badge/PYTHON-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/PYQT6-6.4+-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6">
    <img src="https://img.shields.io/badge/PLATFORM-WINDOWS_10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
    <a href="LICENSE"><img src="https://img.shields.io/badge/LICENSE-CUSTOM_OPEN_SOURCE-orange?style=for-the-badge" alt="License"></a>
    <img src="https://img.shields.io/badge/COVERAGE-80%25-blue?style=for-the-badge&logo=pytest" alt="Coverage">
  </p>
</div>

---

## 📖 项目简介

**WinMsgHub** 是一款基于 Python + PyQt6 开发的 Windows 桌面应用，专为**多源消息聚合、统一管理、智能通知**设计，一站式解决物联网消息、网络推送、本地事件、订阅内容等分散接收的问题。

无论是 MQTT 物联网消息、RSS 新闻订阅、文件变化提醒，还是剪贴板内容、系统硬件事件，WinMsgHub 都能秒级处理并以高度定制化的桌面弹窗展示，同时支持本地数据存储、消息过滤、统计分析等核心能力。

### 💡 为什么选择 WinMsgHub？

- ✅ **多源全覆盖**：支持8类消息源，支持添加多个消息源实例（例如：多MQTT服务器/多监控文件夹等）
- ✅ **极致定制化**：弹窗位置/动画/样式全自定义，你的弹窗你做主
- ✅ **实时高效**：秒级消息处理，配置热重载（修改立即生效，无需重启软件）
- ✅ **安全本地化**：SQLite 本地存储所有数据，还支持纯本地MQTT服务，一键启动
- ✅ **轻量易用**：软件体积极小，可最小化至系统托盘，不占用任务栏，操作界面现代化、易上手

---

## ✨ 核心特性

### 🔌 8大消息源全支持

#### 📡 网络消息源
- **MQTT**（支持 TLS 加密连接）
- **WebSocket** 实时双向通信
- **API** 定时轮询（HTTP/HTTPS）
- **Webhook** 内置服务器接收推送
- **IMAP** 邮件服务器实时监听

#### 💻 本地消息源
- **RSS/Atom** 博客/新闻订阅解析
- **文件监控** 文件夹/文件变化监控（增删改移）
- **剪贴板** 内容实时监控（文本/文件）

> 💡 所有消息源均支持**多实例**和**单独启用/禁用**！

### 🎨 高度可定制的通知弹窗

| 📍 位置定制 | 🎬 动画效果 | 🎨 样式自定义 |
| :---: | :---: | :---: |
| 8个位置可选<br>四角+四边 | 3种动画效果<br>滑入/淡入/缩放<br>支持动画速度调节 | 完全自定义<br>尺寸/透明度/颜色<br>字体/音效 |

### 🌟 其他核心亮点

- 💾 **消息管理**：SQLite本地存储，支持关键词搜索/时间筛选/数据导出
- 🎯 **智能过滤**：自定义过滤规则（包含/排除关键词），只接收重要消息
- 📊 **统计面板**：实时查看消息数量/各源占比/连接状态，支持数据可视化
- 🔔 **系统托盘**：最小化至托盘，支持托盘右键快捷操作/托盘消息提示
- ⚡ **热重载**：所有配置修改立即生效，无需重启应用
- 🔄 **自动更新**：一键检查GitHub最新版本，及时获取新功能
- 📝 **完善日志**：分级日志记录（INFO/DEBUG/ERROR），方便问题排查

---

## 🚀 快速开始

### 📋 系统要求

| 项目 | 要求 |
| :--- | :--- |
| 操作系统 | Windows 10 64位 / Windows 11（推荐） |
| Python 版本 | 3.9 及以上（3.10/3.11 兼容性最佳） |
| 硬件 | 2GB 及以上内存，100MB 及以上磁盘空间 |
| 依赖 | 无额外系统依赖，pip 自动安装所有Python包 |

### 📦 安装与运行

<details>
<summary><b>📥 点击展开 - 安装步骤</b></summary>

<br>

**1. 克隆/下载项目到本地，进入项目根目录**
```bash
cd WinMsgHub
```

**2. 安装项目依赖（建议使用虚拟环境）**
```bash
# 推荐：创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**3. 运行应用（三种方式可选）**
```bash
# 方式1：批处理运行（推荐，自动激活虚拟环境）
run.bat

# 方式2：直接运行（显示控制台日志）
python main.py

# 方式3：无控制台窗口运行
pythonw main.py
```

</details>

### ⚙️ 快速配置消息源

1. 启动应用后，点击左侧导航栏「**消息源配置**」
2. 选择需要配置的消息源类型（如MQTT/文件监控）标签页
3. 点击「**➕ 添加**」按钮，填写配置信息（带*为必填项）
4. 点击「**保存**」，配置**立即生效**（无需重启）！

> 📄 **配置示例**：查看项目内 `config/example_multi_sources.json` 了解所有消息源的完整配置参数。

---

## 📁 项目结构

采用**分层架构**设计（UI层/核心层/数据层/工具层），模块解耦、易扩展，便于后续新增消息源和功能。

<details>
<summary><b>📂 点击展开 - 完整项目结构</b></summary>

```
WinMsgHub/
├── main.py                      # 应用程序入口（初始化/启动）
├── run.bat                      # 快速运行批处理文件
├── requirements.txt             # 项目依赖清单
├── ui/                          # 【UI层】图形界面相关
│   ├── modern_main_window.py    # 主窗口布局与导航
│   ├── tray_icon.py             # 系统托盘图标与右键菜单
│   ├── notification_popup.py    # 通知弹窗核心组件
│   ├── theme_manager.py         # 主题管理（亮色/暗色/自动切换）
│   ├── svg_icons.py             # SVG图标库（手写图标，无Emoji）
│   └── pages/                   # 各功能页面
│       ├── dashboard_page.py    # 仪表盘（统计/状态）
│       ├── sources_page.py      # 消息源配置页面
│       ├── history_page.py      # 消息历史查询/导出
│       ├── popup_page.py        # 弹窗样式/动画配置
│       ├── local_mqtt_page.py   # 本地MQTT服务管理
│       ├── scheduler_page.py    # 定时任务管理
│       ├── settings_page.py     # 系统通用设置
│       └── about_page.py        # 关于页面（版本/更新检查）
├── core/                        # 【核心层】业务逻辑处理
│   ├── config_manager.py        # 配置管理（加载/保存/热重载）
│   ├── connector_manager.py     # 消息源连接器统一管理
│   ├── message_processor.py     # 消息统一处理/分发
│   ├── filter_engine.py         # 消息过滤引擎（规则匹配）
│   ├── popup_manager.py         # 弹窗统一调度/显示
│   ├── local_mqtt_manager.py    # 本地MQTT Broker管理
│   ├── scheduler_manager.py     # 定时任务调度管理
│   └── system_monitor.py        # 系统资源监控
├── data/                        # 【数据层】数据存储与消息源连接
│   ├── database.py              # SQLite数据库操作封装
│   ├── async_database.py        # 异步数据库操作
│   ├── models.py                # 数据模型（消息/配置/统计）
│   └── connectors/              # 各消息源连接器实现
│       ├── base.py              # 连接器基类
│       ├── mqtt_connector.py    # MQTT连接器
│       ├── rss_connector.py     # RSS/Atom连接器
│       ├── file_monitor_connector.py # 文件监控连接器
│       ├── clipboard_connector.py    # 剪贴板监控连接器
│       ├── api_connector.py     # API轮询连接器
│       ├── webhook_connector.py # Webhook服务器连接器
│       ├── websocket_connector.py    # WebSocket连接器
│       ├── imap_connector.py    # IMAP邮件连接器
│       └── error_handler.py     # 连接器错误处理
├── utils/                       # 【工具层】通用工具函数
│   ├── logger.py                # 日志系统（分级记录/文件保存）
│   ├── update_checker.py        # 更新检查器（GitHub Release API）
│   ├── network_utils.py         # 网络工具（IP获取等）
│   ├── async_worker.py          # 异步任务工作器
│   ├── resource_path.py         # 资源路径工具（支持打包）
│   └── single_instance.py       # 单实例锁（防止重复启动）
├── config/                      # 配置文件目录
│   ├── default_config.json      # 默认配置模板
│   ├── example_mqtt_config.json # MQTT配置示例
│   └── example_multi_sources.json # 多消息源配置示例
├── resources/                   # 静态资源（图标/音效）
│   ├── icons/                   # 应用图标
│   └── sounds/                  # 提示音效
└── tests/                       # 单元测试与集成测试
    ├── test_database.py         # 数据库测试
    ├── test_config_manager.py   # 配置管理器测试
    ├── test_mqtt_connector.py   # MQTT连接器测试
    └── test_message_connector.py # 消息连接器测试
```

</details>

---

## 🛠️ 技术栈

| 类别 | 技术/库 | 核心用途 |
| :---: | :--- | :--- |
| **主开发语言** | Python 3.9+ | 应用核心开发，简洁易扩展 |
| **GUI框架** | PyQt6 | 现代化桌面界面，弹窗/托盘/主题/SVG图标支持 |
| **本地存储** | SQLite + sqlite3 | 轻量无服务，存储消息/配置/统计数据 |
| **网络通信** | paho-mqtt / websocket-client / requests / imaplib | MQTT/WebSocket/API/Webhook/IMAP 协议支持 |
| **MQTT服务** | aMQTT | 内置本地MQTT Broker，支持一键启动 |
| **本地监控** | watchdog / pyperclip | 文件监控/剪贴板监听 |
| **解析工具** | feedparser | RSS/Atom 订阅内容解析 |
| **系统监控** | psutil | CPU/内存/磁盘/网络监控 |
| **安全加密** | cryptography | TLS/SSL 加密连接，数据加密 |
| **异步支持** | asyncio / aiofiles | 异步IO操作，提升性能避免卡顿 |
| **版本管理** | packaging | 版本号比较，支持自动更新检查 |
| **测试框架** | pytest + Hypothesis + coverage | 单元测试/属性测试/测试覆盖率统计 |

---

## 📄 开源协议

本项目采用 **自定义开源许可协议**。

[![License](https://img.shields.io/badge/License-Custom_Open_Source-orange?style=flat-square)](LICENSE)

### 📋 协议概要

> ✅ 允许**商业使用** | ✅ 允许**二次开发** | ⚠️ 二次开发**必须开源** | ⚠️ 必须**标明原作者**

### ✅ 允许的使用方式

- ✓ 个人使用和学习
- ✓ 商业使用
- ✓ 修改和二次开发
- ✓ 分发和传播

### ⚠️ 使用条件（必须遵守）

1. **开源要求** - 任何二次开发或衍生作品必须开源
2. **署名要求** - 必须标明原作者：青云制作_彭明航
3. **协议传递** - 衍生作品必须使用相同的许可协议
4. **版权声明** - 不得移除或修改原有版权声明

### ❌ 禁止的行为

- ✗ 闭源发布衍生作品
- ✗ 移除或篡改原作者信息
- ✗ 用于非法用途

### 📝 代码文件版权声明

所有源代码文件必须包含以下版权声明：

```python
"""
WinMsgHub - [模块名称]
作者：青云制作_彭明航
版权所有 - 二次开发必须开源并标明原作者，允许商用
"""
```

### 📖 完整协议

完整的许可协议内容请查看 [LICENSE](LICENSE) 文件。

---

## 👤 作者

<div align="center">
  <h3>青云制作_彭明航</h3>
  <p><b>QQ：2124691573</b></p>
  <p>这是我开源的第二款软件项目，如果它对您有所帮助，希望能给个⭐ Star 支持一下！</p>
  <p>您的支持是项目持续开发的最大动力 💪</p>
</div>

---

## 🙏 致谢

感谢以下优秀的开源项目，WinMsgHub的开发离不开它们的支持：

<div align="center">
  <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/PyQt6-41CD52?logo=qt&logoColor=white" alt="PyQt6"></a>
  <a href="https://www.eclipse.org/paho/"><img src="https://img.shields.io/badge/paho--mqtt-E6522C?logo=eclipse&logoColor=white" alt="paho-mqtt"></a>
  <a href="https://github.com/Yakifo/amqtt"><img src="https://img.shields.io/badge/aMQTT-E6522C?logo=mqtt&logoColor=white" alt="aMQTT"></a>
  <a href="https://github.com/websocket-client/websocket-client"><img src="https://img.shields.io/badge/websocket--client-000000?logo=websocket&logoColor=white" alt="websocket-client"></a>
  <a href="https://github.com/kurtmckee/feedparser"><img src="https://img.shields.io/badge/feedparser-FF6B6B?logo=rss&logoColor=white" alt="feedparser"></a>
  <a href="https://github.com/gorakhargosh/watchdog"><img src="https://img.shields.io/badge/watchdog-3776AB?logo=python&logoColor=white" alt="watchdog"></a>
  <a href="https://github.com/giampaolo/psutil"><img src="https://img.shields.io/badge/psutil-3776AB?logo=python&logoColor=white" alt="psutil"></a>
  <a href="https://hypothesis.readthedocs.io/"><img src="https://img.shields.io/badge/Hypothesis-FF4757?logo=test&logoColor=white" alt="Hypothesis"></a>
  <a href="https://requests.readthedocs.io/"><img src="https://img.shields.io/badge/requests-3776AB?logo=python&logoColor=white" alt="requests"></a>
  <a href="https://pypi.org/project/pyperclip/"><img src="https://img.shields.io/badge/pyperclip-3776AB?logo=python&logoColor=white" alt="pyperclip"></a>
</div>

---

<h3 align="center">☕ 请作者喝杯奶茶 ☕</h3>

<div align="center">
  <img src="resources/images/微信收款码.png" width="200" alt="微信收款码">
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="resources/images/支付宝收款码.jpg" width="183" alt="支付宝收款码">
</div>


---

<div align="center">
  <p>✨ <b>WinMsgHub</b> - 让Windows跨设备接收消息 ✨</p>
  <p>Made with ❤️ by 青云制作_彭明航</p>
  <p><a href="#winmsghub">⬆ 回到顶部</a></p>
</div>
