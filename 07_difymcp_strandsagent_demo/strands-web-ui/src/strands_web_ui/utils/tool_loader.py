"""
Tool loader for the Strands Web UI.

This module provides functions to load and configure tools from the Strands SDK
based on configuration settings, following the patterns from the agent-builder.
"""

import importlib
import logging
import sys
from typing import Dict, Any, List, Optional, Callable

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_tools_from_config(config: Dict[str, Any]) -> List:
    """
    Load tools based on configuration.
    
    Args:
        config: Configuration dictionary with tools section
        
    Returns:
        List of tool objects
    """
    # Get enabled tools from config
    tools_config = config.get("tools", {})
    enabled_tool_names = tools_config.get("enabled", [])
    tool_options = tools_config.get("options", {})
    
    if not enabled_tool_names:
        logger.warning("No tools enabled in configuration")
        return []
    
    # Load all available tools
    enabled_tools = []
    
    # Import strands for the tool decorator
    try:
        from strands import tool as strands_tool
    except ImportError:
        logger.error("Failed to import strands. Make sure it's installed.")
        return []
    
    # Import common tools from strands_tools
    for tool_name in enabled_tool_names:
        try:
            # Try to import the tool directly from its module
            module_name = f"strands_tools.{tool_name}"
            logger.info(f"Attempting to import {module_name}")
            
            # Dynamic import of the module
            module = importlib.import_module(module_name)
            
            # First, look for a function with the same name as the module
            if hasattr(module, tool_name):
                tool_func = getattr(module, tool_name)
                if callable(tool_func):
                    if hasattr(tool_func, 'TOOL_SPEC'):
                        logger.info(f"Found tool '{tool_name}' in module {module_name}")
                        enabled_tools.append(tool_func)
                    else:
                        # Create a wrapper with the @tool decorator
                        logger.info(f"Creating wrapper for tool '{tool_name}'")
                        wrapped_tool = strands_tool(tool_func)
                        enabled_tools.append(wrapped_tool)
                    continue
            
            # If not found by name, look for any function with TOOL_SPEC attribute
            tool_found = False
            for attr_name in dir(module):
                if not attr_name.startswith('_'):
                    attr = getattr(module, attr_name)
                    if callable(attr) and hasattr(attr, 'TOOL_SPEC'):
                        logger.info(f"Found tool '{attr_name}' in module {module_name}")
                        enabled_tools.append(attr)
                        tool_found = True
                        break
            
            # If still not found, look for any callable function that might be the tool
            if not tool_found:
                for attr_name in dir(module):
                    if not attr_name.startswith('_'):
                        attr = getattr(module, attr_name)
                        if callable(attr) and not attr_name.startswith('_') and attr_name not in ['main', 'create_result_table', 'create_error_panel']:
                            # Create a wrapper with the @tool decorator
                            logger.info(f"Creating wrapper for function '{attr_name}' in module {module_name}")
                            wrapped_tool = strands_tool(attr)
                            enabled_tools.append(wrapped_tool)
                            tool_found = True
                            break
                
                if not tool_found:
                    logger.warning(f"No suitable function found in module {module_name}")
                
        except ImportError as e:
            logger.warning(f"Module for tool '{tool_name}' not found: {e}")
        except Exception as e:
            logger.error(f"Error loading tool '{tool_name}': {e}")
    
    # Apply tool-specific configuration if available
    for tool in enabled_tools:
        tool_name = getattr(tool, '__name__', str(tool))
        if tool_name in tool_options:
            logger.info(f"Applying configuration for tool '{tool_name}'")
            # Note: In a real implementation, you might need to handle this differently
            # depending on how the tools are designed to be configured
    
    return enabled_tools

def get_available_tool_names() -> List[str]:
    """
    Get a list of all available tool names from strands_tools and custom tools.
    
    Returns:
        List of tool names
    """
    tool_names = []
    
    try:
        # Get all Python files in the strands_tools directory
        import strands_tools
        import os
        import inspect
        
        # Get the directory where strands_tools is installed
        strands_tools_dir = os.path.dirname(inspect.getfile(strands_tools))
        
        # Get all Python files in the directory
        for file in os.listdir(strands_tools_dir):
            if file.endswith('.py') and not file.startswith('__'):
                tool_name = file[:-3]  # Remove .py extension
                tool_names.append(tool_name)
        
    except ImportError:
        logger.error("Failed to import strands_tools. Make sure it's installed.")
        # Return a default list of common tool names when strands_tools is not available
        tool_names = [
            "calculator",
            "editor",
            "environment",
            "file_read",
            "file_write",
            "http_request",
            "python_repl",
            "shell",
            "think"
        ]
    except Exception as e:
        logger.error(f"Error getting available tool names: {e}")
        tool_names = []
    
    # Add custom tools
    custom_tools = ["audio_transcribe", "supported_languages"]
    tool_names.extend(custom_tools)
    
    return tool_names
