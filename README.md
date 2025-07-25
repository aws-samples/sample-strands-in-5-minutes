# Strands Agents in 5 Minutes / 5分钟上手Strands系列

[English](README_EN.md) | 中文

## 项目介绍
欢迎来到"5分钟上手Strands系列"教程！这是一个专注于提升用户和开发者构建AI Agent能力的系列教程。通过简洁的5分钟教程形式，帮助您快速掌握Strands Agent的设计、开发、集成和部署流程。

## 教程目标
- 通过系列教程提升用户/开发者的Agent构建能力，确保学习的连续性
- 掌握Strands Agent应用的设计、开发、集成和部署的基础流程
- 使用户能够独立开发和部署自己的Agent Demo

## 课程体系
| No. | Session | Description | Demo | Duration | Level | 目录 |
|-----|---------|-------------|------|----------|-------|------|
| 1 | Strands SDK 第一个 Agent | Strands 核心架构 模型/工具/提示、安装 Strands SDK、创建并运行第一个 Strands Agent | 用 Python 代码输出 Strands Agent 的核心组件说明，安装 SDK，运行一个 Strands Agent | 5 min | L100 | [01_first_agent](01_first_agent/) |
| 2 | Strands 会话管理与状态维护 | Strands Loop 简介、会话历史、会话窗口、多轮对话实现 | 用 Strands 实现多轮对话，保存并打印会话历史 | 5 min | L200 | [02_strands_session](02_strands_session/) |
| 3 | Strands 构建自定义的 tool和使用 | Strands 内置工具调用，工具自定义定义与注册 | 开发一个自定义工具（如天气查询）并集成到 Strands Agent 在 Strands Agent 中注册并调用内置工具 | 5 min | L200 | [03_strands_tooluse](03_strands_tooluse/) |
| 4 | Strands 融合 MCP | Strands 中对于MCP Server的发现，集成和使用 | 通过MCP方式注册多个MCP Server 到Agentic 并实现调用 | 5 min | L200 | [04_strands_mcp](04_strands_mcp/) |
| 6 | Strands 与A2A 协议 | 使用A2A协议封装 Strands Agents 实现 Agents 远程协作 | 用Strands 和 A2A SDK开发 remote agents和client agent，实现multi agents 远程协作 | 5 min | L300 | [06_a2a_agents](06_a2a_agents/) |
| 9 | Strands Agent出题机器人 | 基于Strands Agent搭建自动出题机器人 | 用Strands 搭建自动出题机器人Demo，同时可以监测评估Agent执行效率 | 5 min | L400 | |

## 教程特点
- **简洁高效**: 每节控制在5分钟内
- **理论结合实践**: 每个概念都配有实际的Demo
- **循序渐进**: 从基础到进阶，层层递进
- **动手实践**: 每节课程都包含可运行的代码

## 快速开始

### 环境要求
- Python 3.10或更高版本
- 亚马逊云科技账户（用于访问Amazon Bedrock中的Claude 3.7模型）

### 环境搭建
1. 创建并激活Python虚拟环境：
```bash
python -m venv venv
source .venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
uv pip install strands-agents strands-agents-tools
```

### 配置
创建`.env`文件并添加以下内容：
```
AWS_ACCESS_KEY_ID=你的访问密钥ID
AWS_SECRET_ACCESS_KEY=你的秘密访问密钥
AWS_DEFAULT_REGION=你的默认区域（如us-east-1）
```

### 运行示例
```bash
python3 first_agent.py
```

## 课程导航
- [第一课：构建你的第一个Agent](01_first_agent/first_agent.md)
- [第二课：Strands 会话管理与状态维护](02_strands_session/strands-session.py)
- [第三课：Strands 构建自定义的 tool和使用](03_strands_tooluse/strands-tooluse.py)
- [第四课：Strands 融合 MCP](04_strands_mcp/README.md)
- [第六课：Strands 与A2A 协议](06_a2a_agents/)
- [第九课：Strands 搭建自动出题机器人]()

## 参与贡献
欢迎提交Pull Request来帮助改进这个教程系列！

## 安全
更多信息请参见 [CONTRIBUTING](CONTRIBUTING.md) 文件。

## 许可证
本库采用 MIT-0 许可证。详见 [LICENSE](LICENSE) 文件。
