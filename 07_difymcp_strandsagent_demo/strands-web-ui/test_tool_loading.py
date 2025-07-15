#!/usr/bin/env python3
"""
Tool Loading Test Script

This script tests dynamic tool loading and execution in a simple Strands agent.
"""

import importlib
import logging
import sys
from typing import List, Any, Dict, Optional

from strands import Agent, tool
from strands.models import BedrockModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def test_tool(message: str) -> dict:
    """
    A simple test tool to verify tool execution.
    
    Args:
        message: Message to echo
        
    Returns:
        Echo response
    """
    return {
        "status": "success",
        "content": [{"text": f"Test tool received: {message}"}]
    }

def load_tool_from_module(module_name: str, tool_name: Optional[str] = None) -> Any:
    """
    Load a tool function from a module.
    
    Args:
        module_name: Name of the module to import
        tool_name: Name of the tool function (if None, uses module name)
        
    Returns:
        Tool function or None if not found
    """
    try:
        # Import the module
        logger.info(f"Attempting to import {module_name}")
        module = importlib.import_module(module_name)
        
        # If tool_name not provided, use last part of module name
        if tool_name is None:
            tool_name = module_name.split('.')[-1]
        
        # First try: look for function with same name as tool_name
        if hasattr(module, tool_name):
            tool_func = getattr(module, tool_name)
            if callable(tool_func):
                if hasattr(tool_func, 'TOOL_SPEC'):
                    logger.info(f"Found tool '{tool_name}' in module {module_name}")
                    return tool_func
                else:
                    # Create a wrapper with the @tool decorator
                    logger.info(f"Creating wrapper for tool '{tool_name}'")
                    from strands import tool as strands_tool
                    wrapped_tool = strands_tool(tool_func)
                    return wrapped_tool
        
        # Second try: look for any function with TOOL_SPEC
        for attr_name in dir(module):
            if not attr_name.startswith('_'):
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, 'TOOL_SPEC'):
                    logger.info(f"Found tool '{attr_name}' in module {module_name}")
                    return attr
        
        # Third try: look for any callable function
        for attr_name in dir(module):
            if not attr_name.startswith('_'):
                attr = getattr(module, attr_name)
                if callable(attr) and not attr_name.startswith('_') and attr_name not in ['main', 'create_result_table']:
                    # Create a wrapper with the @tool decorator
                    logger.info(f"Creating wrapper for function '{attr_name}' in module {module_name}")
                    from strands import tool as strands_tool
                    wrapped_tool = strands_tool(attr)
                    return wrapped_tool
        
        logger.warning(f"No suitable function found in module {module_name}")
        return None
        
    except ImportError as e:
        logger.error(f"Module {module_name} not found: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading tool from {module_name}: {e}")
        return None

def load_tools(tool_modules: List[str]) -> List:
    """
    Load tools from a list of module names.
    
    Args:
        tool_modules: List of module names to import tools from
        
    Returns:
        List of loaded tool functions
    """
    tools = [test_tool]  # Start with our test tool
    
    for module_name in tool_modules:
        tool_func = load_tool_from_module(module_name)
        if tool_func:
            tools.append(tool_func)
    
    return tools

def test_agent_with_tools(tools: List) -> None:
    """
    Create a test agent with the loaded tools and run some tests.
    
    Args:
        tools: List of tool functions to include in the agent
    """
    try:
        # Create a simple model (you can replace with a mock if needed)
        model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region="us-west-2"
        )
        
        # Create agent with loaded tools
        agent = Agent(
            model=model,
            tools=tools,
            system_prompt="You are a testing assistant. Use the provided tools to demonstrate they work correctly."
        )
        
        # Print available tools
        tool_names = [getattr(t, '__name__', str(t)) for t in tools]
        logger.info(f"Agent loaded with tools: {', '.join(tool_names)}")
        
        # Test our test_tool directly
        logger.info("Testing test_tool...")
        result = agent.tool.test_tool(message="Hello from test script")
        logger.info(f"Result: {result}")
        
        # Test each loaded tool if possible
        for tool in tools:
            if tool == test_tool:
                continue  # Already tested
                
            tool_name = getattr(tool, '__name__', str(tool))
            logger.info(f"Testing tool: {tool_name}")
            
            try:
                # Get the tool method from the agent
                tool_method = getattr(agent.tool, tool_name, None)
                if tool_method:
                    # Try to call with minimal arguments - this will likely fail for most tools
                    # but it will show if the tool is properly registered
                    try:
                        logger.info(f"Tool {tool_name} is available on agent")
                        # We don't actually call the tool as most will need specific arguments
                    except Exception as e:
                        logger.warning(f"Tool {tool_name} requires specific arguments: {e}")
                else:
                    logger.warning(f"Tool {tool_name} not available on agent")
            except Exception as e:
                logger.error(f"Error testing {tool_name}: {e}")
        
        # Test specific tools with appropriate arguments
        try:
            if hasattr(agent.tool, "calculator"):
                logger.info("Testing calculator tool...")
                result = agent.tool.calculator(expression="2+2")
                logger.info(f"Calculator result: {result}")
        except Exception as e:
            logger.error(f"Error testing calculator: {e}")
            
        try:
            if hasattr(agent.tool, "shell"):
                logger.info("Testing shell tool...")
                result = agent.tool.shell(command="ls -la")
                logger.info(f"Shell result: {result}")
        except Exception as e:
            logger.error(f"Error testing shell: {e}")
            
        try:
            if hasattr(agent.tool, "file_read"):
                logger.info("Testing file_read tool...")
                result = agent.tool.file_read(path=".", mode="find")
                logger.info(f"File_read result: {result}")
        except Exception as e:
            logger.error(f"Error testing file_read: {e}")
        
    except Exception as e:
        logger.error(f"Error in test_agent_with_tools: {e}")

def main():
    """Main function to run the test."""
    # List of tool modules to test
    tool_modules = [
        "strands_tools.calculator",
        "strands_tools.editor",
        "strands_tools.environment",
        "strands_tools.file_read",
        "strands_tools.file_write",
        "strands_tools.http_request",
        "strands_tools.python_repl",
        "strands_tools.shell",
        "strands_tools.think"
    ]
    
    # Load tools
    loaded_tools = load_tools(tool_modules)
    logger.info(f"Loaded {len(loaded_tools)} tools")
    
    # Test agent with loaded tools
    test_agent_with_tools(loaded_tools)

if __name__ == "__main__":
    main()
