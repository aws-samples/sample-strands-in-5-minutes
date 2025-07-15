"""
Tests for the configuration loader.
"""

import os
import json
import tempfile
import unittest

from strands_web_ui.utils.config_loader import load_config, load_mcp_config


class TestConfigLoader(unittest.TestCase):
    """Tests for the configuration loader."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w+')
        self.temp_config.write(json.dumps({
            "model": {
                "provider": "test-provider",
                "model_id": "test-model",
                "region": "test-region",
                "max_tokens": 1000
            },
            "agent": {
                "system_prompt": "Test prompt",
                "max_parallel_tools": 2,
                "record_direct_tool_call": False,
                "hot_reload_tools": False,
                "enable_native_thinking": False
            },
            "conversation": {
                "window_size": 10,
                "summarize_overflow": False
            },
            "ui": {
                "update_interval": 0.5
            }
        }))
        self.temp_config.close()
        
        # Create a temporary MCP config file
        self.temp_mcp_config = tempfile.NamedTemporaryFile(delete=False, mode='w+')
        self.temp_mcp_config.write(json.dumps({
            "mcpServers": {
                "test-server": {
                    "command": "echo",
                    "args": ["hello"],
                    "env": {}
                }
            }
        }))
        self.temp_mcp_config.close()
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.unlink(self.temp_config.name)
        os.unlink(self.temp_mcp_config.name)
    
    def test_load_config(self):
        """Test loading configuration from a file."""
        config = load_config(self.temp_config.name)
        self.assertEqual(config["model"]["provider"], "test-provider")
        self.assertEqual(config["model"]["model_id"], "test-model")
        self.assertEqual(config["agent"]["system_prompt"], "Test prompt")
        self.assertEqual(config["conversation"]["window_size"], 10)
        self.assertEqual(config["ui"]["update_interval"], 0.5)
    
    def test_load_config_default(self):
        """Test loading default configuration when file not found."""
        config = load_config("non_existent_file.json")
        self.assertEqual(config["model"]["provider"], "bedrock")
        self.assertTrue(config["agent"]["enable_native_thinking"])
        self.assertEqual(config["conversation"]["window_size"], 20)
    
    def test_load_mcp_config(self):
        """Test loading MCP configuration from a file."""
        config = load_mcp_config(self.temp_mcp_config.name)
        self.assertIn("mcpServers", config)
        self.assertIn("test-server", config["mcpServers"])
        self.assertEqual(config["mcpServers"]["test-server"]["command"], "echo")
    
    def test_load_mcp_config_default(self):
        """Test loading default MCP configuration when file not found."""
        config = load_mcp_config("non_existent_file.json")
        self.assertIn("mcpServers", config)
        self.assertEqual(len(config["mcpServers"]), 0)


if __name__ == "__main__":
    unittest.main()
