"""
Tests for the MCP server manager.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from strands_web_ui.mcp_server_manager import MCPServerManager


class TestMCPServerManager(unittest.TestCase):
    """Tests for the MCP server manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = MCPServerManager()
        
        # Create a temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w+')
        self.temp_config.write(json.dumps({
            "mcpServers": {
                "test-server": {
                    "command": "echo",
                    "args": ["hello"],
                    "env": {}
                },
                "disabled-server": {
                    "command": "echo",
                    "args": ["disabled"],
                    "env": {},
                    "disabled": True
                }
            }
        }))
        self.temp_config.close()
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.unlink(self.temp_config.name)
    
    def test_load_config(self):
        """Test loading configuration from a file."""
        result = self.manager.load_config(self.temp_config.name)
        self.assertTrue(result)
        self.assertIn("test-server", self.manager.servers)
        self.assertNotIn("disabled-server", self.manager.servers)
    
    def test_load_config_file_not_found(self):
        """Test loading configuration from a non-existent file."""
        result = self.manager.load_config("non_existent_file.json")
        self.assertFalse(result)
    
    def test_get_server_ids(self):
        """Test getting server IDs."""
        self.manager.load_config(self.temp_config.name)
        server_ids = self.manager.get_server_ids()
        self.assertEqual(server_ids, ["test-server"])
    
    def test_get_server_status(self):
        """Test getting server status."""
        self.manager.load_config(self.temp_config.name)
        status = self.manager.get_server_status("test-server")
        self.assertTrue(status["exists"])
        self.assertFalse(status["connected"])
        self.assertEqual(status["command"], "echo")
        
        # Test non-existent server
        status = self.manager.get_server_status("non-existent-server")
        self.assertFalse(status.get("exists", True))
    
    @patch("strands_web_ui.mcp_server_manager.MCPClient")
    @patch("strands_web_ui.mcp_server_manager.stdio_client")
    def test_connect_server(self, mock_stdio_client, mock_mcp_client):
        """Test connecting to a server."""
        # Set up mocks
        mock_server = MagicMock()
        mock_mcp_client.return_value = mock_server
        
        # Load config and connect
        self.manager.load_config(self.temp_config.name)
        result = self.manager.connect_server("test-server")
        
        # Check results
        self.assertTrue(result)
        self.assertIn("test-server", self.manager.active_servers)
        mock_server.start.assert_called_once()
    
    @patch("strands_web_ui.mcp_server_manager.MCPClient")
    @patch("strands_web_ui.mcp_server_manager.stdio_client")
    def test_disconnect_server(self, mock_stdio_client, mock_mcp_client):
        """Test disconnecting from a server."""
        # Set up mocks
        mock_server = MagicMock()
        mock_mcp_client.return_value = mock_server
        
        # Load config and connect
        self.manager.load_config(self.temp_config.name)
        self.manager.connect_server("test-server")
        
        # Disconnect
        result = self.manager.disconnect_server("test-server")
        
        # Check results
        self.assertTrue(result)
        self.assertNotIn("test-server", self.manager.active_servers)
        mock_server.stop.assert_called_once()
    
    def test_disconnect_non_existent_server(self):
        """Test disconnecting from a non-existent server."""
        result = self.manager.disconnect_server("non-existent-server")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
