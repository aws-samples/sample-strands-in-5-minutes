"""
Configuration loader for the Strands Web UI.
"""

import json
import os
from typing import Dict, Any


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file. If not provided, 
                    will load config/config.json.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    if not config_path:
        config_path = "config/config.json"
    
    try:
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
    
    # Return default config if file not found or error occurred
    return {
        "model": {
            "provider": "bedrock",
            "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "region": "us-east-1",
            "max_tokens": 24000
        },
        "agent": {
            "system_prompt": "You are a helpful assistant that provides concise, accurate information.",
            "max_parallel_tools": 4,
            "record_direct_tool_call": True,
            "hot_reload_tools": True,
            "enable_native_thinking": True,
            "thinking_budget": 16000
        },
        "conversation": {
            "window_size": 20,
            "summarize_overflow": True
        },
        "ui": {
            "update_interval": 0.1
        }
    }


def load_mcp_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load MCP server configuration from a JSON file.
    
    Args:
        config_path: Path to the MCP configuration file. If not provided, 
                    will load config/mcp_config.json.
    
    Returns:
        Dict[str, Any]: MCP configuration dictionary
    """
    if not config_path:
        config_path = "config/mcp_config.json"
    
    try:
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading MCP config from {config_path}: {e}")
    
    # Return empty config if file not found or error occurred
    return {"mcpServers": {}}
