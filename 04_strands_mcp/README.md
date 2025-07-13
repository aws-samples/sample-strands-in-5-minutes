# Strands Agents MCP 集成指南

欢迎来到 Strands in 5 minutes 快速上手系列！今天我们将学习如何使用 Strands Agents 集成 MCP（模型上下文协议），让 AI Agent 轻松调用外部工具和服务，扩展Agent 能力。

## 什么是 MCP？
MCP（Model Context Protocol）是一种开放协议，标准化了 AI Agent 与外部工具和服务的交互方式。它像一个“万能插座”，让 Agent 无需关心服务细节，就能调用数据库、API、文件系统等多种工具。Strands Agents 内置对 MCP 的支持，能轻松连接 MCP 服务器，自动发现和调用其提供的工具。

## MCP 作用
- **统一接口**：不同服务用同一协议接入，简化集成复杂度
- **多语言&多平台**：支持任意语言编写的服务，支持本地、云端多种部署
- **动态发现工具**：Agent 启动时自动获取 MCP 服务器上的所有工具
- **安全可靠**：通过上下文管理确保连接生命周期和资源释放

## Strands Agents 的 MCP 优势

- **MCP Server 构建** - 使用 `FastMCP` 快速创建服务器  
- **MCP Client 集成** - 一行代码连接任何 MCP 服务  
- **工具自动发现** - 自动获取远程工具  
- **无缝集成** - Agent 透明调用远程服务

## Strands 支持的 MCP Server 连接方式

| 连接方式               | 说明                                             |
|------------------------|--------------------------------------------------|
| **标准输入输出（stdio）** | 适合本地进程间通信，基于标准输入输出流交换数据           |
| **Streamable HTTP**     | 基于 HTTP 协议的流式事件传输，适合网络服务调用             |
| **Server-Sent Events (SSE)** | 基于 SSE 的事件推送方式，支持服务器主动推送消息           |
| **自定义传输协议**       | 高级用户可实现自定义的 MCP 传输协议，满足特殊需求             |


## Demo 介绍
本 Demo 展示了一个基于MCP的美食菜谱智能Agent，它由提供美食菜谱数据服务的MCP Server和作为Client的Agent组成，通过MCP获取菜谱信息，实现菜系查询、菜谱推荐、食材搜索等核心功能。


![Demo 架构图](mcp_architecture.png)


## Demo 流程
### 1. 构建 MCP Server

Strands 内置 FastMCP，让你轻松创建 MCP 服务器。以美食MCP Server为例：

```python
from mcp.server import FastMCP

# 1. 创建 MCP 服务器实例
mcp = FastMCP(name="Chinese Cuisine Recipe Service", host="0.0.0.0", port=8080)

# 2. 准备数据源
RECIPE_CATALOG = {
    "sichuan": {"title": "川菜", "recipes": [...]},
    "cantonese": {"title": "粤菜", "recipes": [...]},
    # ... 更多菜系数据
}

# 3. 定义工具函数，采用`@mcp.tool()` 自动将函数暴露为 MCP 工具
@mcp.tool()
def list_cuisines() -> dict:
    """列出所有可用的中餐菜系"""
    return {"available_cuisines": {...}}

@mcp.tool() 
def get_recipes_by_cuisine(cuisine: str) -> dict:
    """获取指定菜系的菜谱"""
    return RECIPE_CATALOG.get(cuisine.lower(), {})

@mcp.tool()
def search_recipes_by_ingredient(ingredient: str) -> dict:
    """根据食材搜索相关菜谱"""
    return {"matching_recipes": [...]}

# 4. 启动服务器
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### 2. 启动MCP Server

```bash
python strands_mcp_server.py
```
启动后显示如下
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```
**保持服务器运行**，Agent 需要连接到此服务，查询菜谱数据



### 3. 创建菜谱Agent

 `strands_cooking_agent.py`：

```python

# 连接 MCP 服务器
mcp_client = MCPClient(lambda: streamablehttp_client("http://localhost:8080/mcp"))

with mcp_client:
    # 创建 Agent 并注册 MCP 工具
    agent = Agent(model=model, system_prompt="你是中华美食专家...")
    mcp_tools = mcp_client.list_tools_sync()
    agent.tool_registry.process_tools(mcp_tools)
    
    # 开始交互
    while True:
        user_input = input("\n您的需求: ")
        if user_input.lower() in ["exit", "退出"]:
            break
        agent(user_input)

```

### 4. 运行 Agent
在新终端启动（保持服务器运行）：
```bash
python strands_cooking_agent.py
```

Agent 启动后会显示详细的工具发现过程：
```
Connecting to MCP Server...
🔍 正在发现 MCP 服务器上的工具...
✅ 发现 3 个可用工具:
   1. list_cuisines - 列出所有可用的中餐菜系
   2. get_recipes_by_cuisine - 获取指定菜系的菜谱
   3. search_recipes_by_ingredient - 根据食材搜索相关菜谱

🔧 正在注册工具到 Agent...
✅ 工具注册完成！

🍳 中华美食专家 - MCP 集成版
==================================================
🥢 试试问：'有哪些菜系？' 或 '推荐一道川菜' 或 '用猪肉能做什么菜？'
```

### 工具调用实时监控
当用户提问时，控制台会实时显示工具调用过程：
```
您的需求: 有哪些菜系？

正在为您查找...

🤖 Agent 开始处理您的请求...
🛠️  调用工具: list_cuisines
📤 结果: {'available_cuisines': {'sichuan': {'title': '川菜', 'recipe_count': 2}, ...}}
----------------------------------------
📊 本次共调用了 1 个工具
```

### 5. 测试 Agent

**测试1：查询菜系功能**
```
有哪些菜系？
```

**测试2：菜谱推荐功能**
```
推荐一道川菜
```

**测试3：食材搜索功能**
```
用猪肉能做什么菜？
```

## 总结
在本教程中，我们已经：  

✅ 构建了一个简单的 MCP 服务器，演示外部服务集成  
✅ 以最少代码将 Agent 连接到 MCP 服务器  
✅ 实现了通过自然语言的无缝工具调用  
✅ 理解了 Strands Agents SDK 如何简化了 MCP 的复杂性 

Strands Agents + MCP 让 AI Agent 具备了即插即用、跨语言、跨平台、多服务组合的强大能力。只需几行代码，通过 MCP 即可让 Strands 连接丰富的外部工具，快速构建智能体应用。