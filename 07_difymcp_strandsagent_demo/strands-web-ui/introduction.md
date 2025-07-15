# Strands Web UI 介绍

## Strands Web UI示例概述

Strands Web UI是一个基于Streamlit构建的Web界面，集成了Strands Agents SDK的核心功能，为AI智能体提供可视化交互环境。该项目展示了如何将Strands SDK的智能体能力与Web界面结合，实现更直观的用户交互体验。

### 功能特点

- 基于Streamlit的交互式聊天界面，支持实时流式响应
- 智能体思考过程可视化，展示Strands SDK的思维链能力
- 通过控制台日志记录工具调用和执行过程
- MCP (Model Context Protocol)服务器集成，扩展智能体工具集
- 可配置的模型参数和智能体设置
- 基于Strands SDK的对话历史管理

## 开发目的

该示例主要用于：

1. 展示Strands Agents SDK在Web应用中的实际应用方式
2. 提供一个参考实现，说明如何处理Strands智能体的流式输出和思考过程
3. 演示Strands SDK与MCP协议的集成方法
4. 为开发者提供一个可扩展的基础框架，用于构建自己的智能体Web应用

## Strands SDK集成实现

### 智能体初始化与配置

Strands Web UI利用Strands SDK的灵活性，实现了可配置的智能体初始化：

```python
def initialize_agent(config, mcp_manager=None):
    # 创建模型
    model_config = config.get("model", {})
    model = BedrockModel(
        model_id=model_config.get("model_id", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
        region=model_config.get("region", "us-east-1"),
        additional_request_fields=additional_request_fields
    )
    
    # 创建对话管理器
    conversation_manager = SlidingWindowConversationManager(
        window_size=conversation_config.get("window_size", 20)
    )
    
    # 初始化智能体
    return Agent(
        model=model,
        system_prompt=agent_config.get("system_prompt"),
        tools=tools,
        conversation_manager=conversation_manager,
        # 其他参数...
    )
```

这种方法充分利用了Strands SDK的模块化设计，允许独立配置模型、工具和对话管理器。

### 对话管理实现

Strands Web UI结合Strands SDK的`SlidingWindowConversationManager`和Streamlit的会话状态，实现了高效的对话管理：

```python
# Strands SDK对话管理
conversation_manager = SlidingWindowConversationManager(window_size=window_size)

# Streamlit会话状态管理
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
```

这种实现利用了Strands SDK的对话管理能力来维护智能体的上下文窗口，同时使用Streamlit的会话状态来持久化UI显示。

### 预构建工具集成

Strands SDK提供了丰富的预构建工具集，Strands Web UI示例展示了如何有效地集成和使用这些工具：

#### 1. 导入预构建工具

示例直接从`strands_tools`包导入多种预构建工具：

```python
# 导入预构建工具
from strands_tools import (
    calculator,    # 数学计算工具
    editor,        # 文本编辑工具
    environment,   # 环境变量工具
    file_read,     # 文件读取工具
    file_write,    # 文件写入工具
    http_request,  # HTTP请求工具
    python_repl,   # Python解释器工具
    shell,         # 命令行工具
    think,         # 思考工具
    workflow       # 工作流工具
)
```

这些工具涵盖了常见的功能需求，使智能体能够执行各种操作，从简单的计算到复杂的文件操作和HTTP请求。

#### 2. 工具映射与配置

示例实现了一个灵活的工具配置系统，允许通过UI或配置文件选择启用哪些工具：

```python
# 将工具名称映射到实际工具对象
tool_map = {
    "calculator": calculator,
    "editor": editor,
    "environment": environment,
    "file_read": file_read,
    "file_write": file_write,
    "http_request": http_request,
    "python_repl": python_repl,
    "shell": shell,
    "think": think,
    "workflow": workflow
}

# 基于配置选择工具
tools = [search_knowledge_base]  # 从自定义工具开始
for tool_name in enabled_tool_names:
    if tool_name in tool_map:
        tools.append(tool_map[tool_name])
        logger.info(f"Added tool: {tool_name}")
```

#### 3. UI工具选择

示例提供了一个直观的UI界面，让用户可以选择启用哪些工具：

```python
# 获取所有可用工具名称
available_tool_names = get_available_tool_names()

# 获取当前启用的工具
enabled_tools = config.get("tools", {}).get("enabled", [])

# 创建工具选择的多选框
selected_tools = st.multiselect(
    "Enabled Tools",
    options=available_tool_names,
    default=valid_enabled_tools,
    help="Select the tools you want to enable"
)
```

这种方法使用户可以根据需要动态调整智能体的能力，而无需修改代码。

#### 4. 工具热重载

示例支持工具的热重载，使开发者可以在不重启应用的情况下添加或修改工具：

```python
# 初始化智能体时启用热重载
agent = Agent(
    # 其他参数...
    load_tools_from_directory=agent_config.get("hot_reload_tools", True),
    # 其他参数...
)
```

这一功能特别适合开发和测试场景，可以快速迭代工具功能。

#### 5. 自定义工具示例

除了使用预构建工具外，示例还展示了如何创建自定义工具：

```python
@tool
def search_knowledge_base(query: str) -> dict:
    """
    Search the knowledge base for information.
    
    Args:
        query: The search query
        
    Returns:
        Relevant information from the knowledge base
    """
    # 模拟搜索延迟
    time.sleep(1)
    return {
        "status": "success",
        "content": [{"text": f"Found information about: {query}. This is simulated knowledge base content."}]
    }
```

这个示例展示了Strands SDK的`@tool`装饰器如何简化工具创建过程，只需定义一个带有类型注解和文档字符串的函数即可。

### 思考过程可视化

Strands SDK支持捕获智能体的思考过程，Web UI通过自定义处理程序实现了这一过程的可视化：

```python
def _handle_thinking_content(self, reasoning_text):
    # 提取思考文本
    if isinstance(reasoning_text, dict) and "text" in reasoning_text:
        thinking_text = reasoning_text["text"]
    elif isinstance(reasoning_text, str):
        thinking_text = reasoning_text
    else:
        thinking_text = str(reasoning_text)
    
    # 添加到思考容器
    self.thinking_container += thinking_text
    
    # 更新UI
    if self.thinking_placeholder:
        self.thinking_placeholder.markdown(f"""
        <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px;">
        {self.thinking_container}
        </div>
        """, unsafe_allow_html=True)
```

这一实现展示了如何利用Strands SDK的事件回调机制来捕获和展示智能体的内部思考过程。

### MCP集成的两层实现

Strands Web UI示例中的MCP集成采用了两层架构，充分利用了Strands SDK的内置MCP支持：

#### 1. Strands SDK的MCPClient层

Strands SDK内置了对MCP的支持，通过`strands.tools.mcp`模块提供了`MCPClient`类：

```python
from strands.tools.mcp import MCPClient
```

这个内置客户端提供了基础的MCP功能：
- 连接到MCP服务器
- 获取服务器提供的工具列表
- 将MCP工具转换为Strands Agent可用的工具格式
- 处理工具调用和结果

在示例中，MCPClient的使用如下：

```python
# 创建带有stdio传输的MCP客户端
from mcp import stdio_client
server = MCPClient(lambda: stdio_client(params))

# 启动服务器
server.start()
```

#### 2. MCPServerManager层

在Strands SDK的MCPClient基础上，示例实现了一个更高级的`MCPServerManager`类，提供了额外的管理功能：

```python
class MCPServerManager:
    """
    管理MCP服务器连接和工具。
    
    此类处理：
    - 从配置文件加载MCP服务器配置
    - 连接和断开MCP服务器
    - 从MCP服务器检索工具
    - 管理服务器状态
    """
```

MCPServerManager提供了以下增强功能：
- 管理多个MCP服务器连接
- 从配置文件加载服务器设置
- 提供服务器状态管理和UI集成
- 简化工具获取和集成流程

这种两层架构的优势在于：
1. 利用了Strands SDK的内置MCP支持，无需重新实现基础功能
2. 提供了更高级的管理功能，使MCP服务器的使用更加灵活和方便
3. 实现了与UI的无缝集成，使用户可以通过界面控制MCP服务器

工具集成的实现如下：

```python
# 获取MCP工具
if mcp_manager:
    mcp_tools = mcp_manager.get_all_tools()
    tools.extend(mcp_tools)
```

这种方法使得智能体可以无缝使用来自MCP服务器的工具，扩展了其能力范围。

### 流式响应处理

Strands SDK支持流式输出，Web UI通过自定义处理程序实现了实时更新：

```python
def _handle_text_streaming(self, kwargs):
    text_chunk = None
    
    # 从事件中提取文本
    if "content_block_delta" in kwargs:
        delta = kwargs["content_block_delta"]
        if "delta" in delta and "text" in delta["delta"]:
            text_chunk = delta["delta"]["text"]
    
    # 更新UI
    if text_chunk:
        self.message_container += text_chunk
        self._update_ui_if_needed()
```

这种实现利用了Strands SDK的事件驱动架构，实现了流畅的实时响应体验。

## 技术实现要点

1. **事件驱动架构**：利用Strands SDK的回调机制处理各种事件（思考、流式输出、工具调用）

2. **模型配置灵活性**：展示了如何配置Strands SDK支持的不同模型和参数

3. **工具扩展性**：结合预构建工具、自定义工具和MCP工具，展示Strands SDK的工具扩展能力

4. **两层MCP集成**：利用Strands SDK的内置MCPClient并在其基础上构建更高级的管理功能

5. **对话管理**：利用Strands SDK的对话管理器实现上下文维护

6. **日志记录**：通过控制台日志记录工具执行过程，便于调试和监控

```python
# 工具执行日志
print("\n===== TOOL EXECUTION LOGS =====")
print(f"Processing user input: {user_input}")
print(f"Available tools on agent: {', '.join(tool_names)}")
print("Calling agent with user input...")
response = agent(user_input)
print(f"Agent response: {response}")
print("===== END TOOL EXECUTION LOGS =====\n")
```

这个示例展示了如何有效地将Strands Agents SDK集成到Web应用中，利用其核心功能构建交互式智能体界面。通过这种集成，开发者可以快速构建具有高级AI能力的Web应用，同时保持代码的简洁性和可维护性。
