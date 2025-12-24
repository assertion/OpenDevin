# OpenHands：AI驱动的软件开发代理平台架构深度解析

> 探索OpenHands（原OpenDevin）如何通过精心设计的架构，让AI代理像人类开发者一样编写代码、运行命令、浏览网页，甚至从StackOverflow复制代码片段。

## 引言

在AI快速发展的今天，自动化软件开发已成为一个热门话题。OpenHands作为一个开源的AI软件开发代理平台，通过其独特的架构设计，实现了让AI代理完成复杂软件开发任务的能力。本文将深入解析OpenHands的架构设计，帮助开发者理解这个强大系统的内部工作原理。

## 项目概览

OpenHands（前身为OpenDevin）是一个由AI驱动的软件开发代理平台，其核心理念是"Code Less, Make More"（少写代码，多创造价值）。该项目采用Python后端和TypeScript前端的架构，通过Docker容器化部署，支持多种LLM提供商。

## 核心架构设计

### 1. 整体架构概览

OpenHands采用事件驱动架构，整个系统围绕**EventStream（事件流）**构建。EventStream作为系统的核心通信枢纽，所有组件都通过它进行消息传递和协作。

```
┌─────────────┐
│   Frontend  │ (TypeScript/React)
└──────┬──────┘
       │ WebSocket
       ▼
┌─────────────────────────────────────┐
│         Server (FastAPI)            │
│  ┌───────────────────────────────┐  │
│  │    SessionManager             │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │   AgentSession          │  │  │
│  │  │  ┌───────────────────┐  │  │  │
│  │  │  │ AgentController   │  │  │  │
│  │  │  └───────────────────┘  │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │ EventStream
               ▼
┌─────────────────────────────────────┐
│         Runtime (Docker)            │
│  ┌───────────────────────────────┐  │
│  │   ActionExecutor              │  │
│  │   - Bash Sandbox              │  │
│  │   - BrowserEnv                │  │
│  │   - File Operations           │  │
│  │   - Plugin System             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 2. 核心组件详解

#### 2.1 Agent（代理）

Agent是OpenHands的核心执行单元，负责根据当前状态（State）生成动作（Action），推动任务向前执行。OpenHands支持多种Agent实现：

- **CodeActAgent**：代码执行代理，擅长编写和执行代码
- **BrowsingAgent**：浏览代理，专门处理网页浏览任务
- **PlannerAgent**：规划代理，负责任务分解和规划
- **DelegatorAgent**：委托代理，可以将任务分配给其他代理
- **Micro Agents**：微代理，包括代码审查、数学计算、PostgreSQL操作等专门化代理

每个Agent都实现了`step`方法，该方法接收当前State，返回一个Action，推动任务向前一步。

#### 2.2 AgentController（代理控制器）

AgentController是Agent的执行引擎，负责：

- **初始化Agent**：根据配置创建和初始化Agent实例
- **管理State**：维护Agent的当前状态，包括任务历史、计划、迭代计数等
- **驱动主循环**：执行核心控制循环，推动Agent逐步完成任务
- **处理委托**：管理多代理系统中的任务委托和协调

核心控制循环的伪代码：

```python
while True:
    prompt = agent.generate_prompt(state)
    response = llm.completion(prompt)
    action = agent.parse_response(response)
    observation = runtime.run(action)
    state = state.update(action, observation)
```

#### 2.3 State（状态）

State对象代表Agent的当前运行状态，包含：

- **多代理状态**：根任务、子任务、全局/本地迭代计数、委托层级
- **运行状态**：当前Agent状态（LOADING、RUNNING、PAUSED等）、流量控制状态、确认模式
- **历史记录**：事件历史，包括Agent采取的动作和观察结果
- **指标数据**：全局和本地任务指标
- **额外数据**：任务特定的额外信息

State使用pickle进行序列化，支持会话的保存和恢复。

#### 2.4 EventStream（事件流）

EventStream是OpenHands架构的通信骨干，采用发布-订阅模式：

- **Actions（动作）**：Agent发出的请求，如编辑文件、运行命令、发送消息
- **Observations（观察）**：环境返回的信息，如文件内容、命令输出、错误信息

所有组件都通过EventStream进行通信，实现了松耦合的架构设计。

#### 2.5 Runtime（运行时）

Runtime负责执行Actions并返回Observations。OpenHands支持多种Runtime实现：

**EventStream Runtime（默认）**：
- 使用Docker容器为每个会话创建隔离环境
- 在容器内执行动作
- 支持直接文件系统访问
- 适合开发、测试和需要完全控制执行环境的场景

**Remote Runtime**：
- 连接到远程服务器上的ActionExecutor
- 通过发送请求到远程客户端执行动作
- 支持分布式执行和云部署
- 适合生产环境、可扩展性和资源受限场景

Runtime的核心功能包括：
- Bash沙箱执行
- 浏览器交互（通过BrowserEnv）
- 文件系统操作
- 环境变量管理
- 插件管理（Jupyter、AgentSkills等）

#### 2.6 Server（服务器）

Server基于FastAPI构建，提供WebSocket和HTTP API接口：

**主要组件**：
- **Session**：管理WebSocket连接，处理客户端与Agent之间的通信
- **AgentSession**：管理Agent的生命周期，包括运行时环境、Agent控制器和安全分析器
- **SessionManager**：管理多个客户端会话，处理会话的添加、重启和清理

**API端点**：
- WebSocket连接：实时双向通信
- 文件上传：支持文件上传和验证
- Agent交互：启动任务、发送消息等
- 安全分析：安全相关的API请求

#### 2.7 Frontend（前端）

前端采用TypeScript和React构建，提供现代化的Web界面：

- **实时通信**：通过WebSocket与后端实时通信
- **文件浏览器**：可视化文件系统操作
- **终端界面**：显示命令执行结果
- **聊天界面**：与Agent交互的对话界面
- **设置管理**：配置模型、工作区等

### 3. 数据流和交互流程

#### 3.1 任务执行流程

1. **用户发起任务**：用户通过前端界面或API发送任务请求
2. **Session初始化**：Server创建新的Session和AgentSession
3. **Agent初始化**：根据配置创建Agent和Runtime
4. **控制循环启动**：AgentController开始执行控制循环
5. **动作生成**：Agent根据State生成Action
6. **动作执行**：Runtime执行Action并返回Observation
7. **状态更新**：State根据Action和Observation更新
8. **循环继续**：重复步骤5-7，直到任务完成或出错

#### 3.2 多代理协作流程

OpenHands支持多代理协作，通过委托机制实现：

```
任务开始（子任务0）
  ↓
CodeActAgent: 需要BrowsingAgent帮助
  ↓
委托开始（子任务1）
  ↓
BrowsingAgent: 执行浏览任务
  ↓
委托结束（子任务1）
  ↓
CodeActAgent: 接收结果并完成任务
  ↓
任务结束（子任务0）
```

### 4. 关键技术特性

#### 4.1 插件系统

OpenHands采用插件架构，支持扩展功能：

- **Jupyter插件**：支持交互式Python代码执行
- **AgentSkills插件**：提供文件编辑、文件操作、文件读取等技能
- **自定义插件**：开发者可以轻松添加自定义插件

#### 4.2 安全机制

- **沙箱隔离**：所有代码执行都在Docker容器中进行
- **安全分析器**：可选的代码安全检查
- **权限控制**：细粒度的文件系统访问控制

#### 4.3 存储系统

支持多种存储后端：
- **本地存储**：本地文件系统
- **S3存储**：AWS S3兼容存储
- **Google Cloud存储**：GCS存储
- **内存存储**：临时数据存储

#### 4.4 LLM集成

通过LiteLLM支持多种LLM提供商：
- Anthropic Claude
- OpenAI GPT
- Google Gemini
- 以及其他兼容OpenAI API的模型

### 5. 部署架构

OpenHands支持多种部署方式：

#### 5.1 Docker部署（推荐）

```bash
docker run -it --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.12-nikolaik \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:0.12
```

#### 5.2 Docker Compose部署

使用`compose.yml`文件可以快速启动完整的OpenHands环境。

#### 5.3 开发环境

支持本地开发模式，前后端分离运行，便于开发和调试。

### 6. 架构优势

1. **松耦合设计**：通过EventStream实现组件间的松耦合，易于扩展和维护
2. **多代理支持**：支持复杂的多代理协作场景
3. **可扩展性**：插件系统使得功能扩展变得简单
4. **安全性**：沙箱隔离确保代码执行安全
5. **灵活性**：支持多种Runtime、存储和LLM提供商
6. **实时性**：WebSocket实现实时双向通信

### 7. 技术栈总结

**后端**：
- Python 3.12+
- FastAPI（Web框架）
- LiteLLM（LLM抽象层）
- Docker（容器化）
- Poetry（依赖管理）

**前端**：
- TypeScript
- React
- Vite（构建工具）
- Tailwind CSS（样式）

**基础设施**：
- Docker/Docker Compose
- WebSocket（实时通信）
- EventStream（事件系统）

## 总结

OpenHands通过精心设计的架构，实现了AI代理的复杂软件开发能力。其事件驱动架构、多代理协作机制、插件系统和安全隔离设计，使得系统既强大又灵活。无论是作为研究平台、开发工具还是生产系统，OpenHands都展现出了优秀的架构设计理念。

对于开发者而言，理解OpenHands的架构不仅有助于更好地使用这个平台，也能为构建类似的AI系统提供宝贵的参考。随着AI技术的不断发展，OpenHands的架构设计将继续演进，为AI辅助软件开发开辟新的可能性。

---

**相关资源**：
- GitHub: https://github.com/All-Hands-AI/OpenHands
- 文档: https://docs.all-hands.dev
- 论文: https://arxiv.org/abs/2407.16741

**作者注**：本文基于OpenHands 0.12版本，架构细节可能随版本更新而变化，建议参考最新官方文档。
