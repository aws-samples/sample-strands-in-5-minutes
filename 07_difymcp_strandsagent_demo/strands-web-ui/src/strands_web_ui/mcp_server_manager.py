"""
MCP Server Manager for Strands Web UI

This module provides a manager class for MCP servers that can be used with Strands agents.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any

from mcp import StdioServerParameters
from strands.tools.mcp import MCPClient
from strands.types.tools import AgentTool

logger = logging.getLogger(__name__)

class MCPServerManager:
    """
    Manages MCP server connections and tools.
    
    This class handles:
    - Loading MCP server configurations from a config file
    - Connecting to and disconnecting from MCP servers
    - Retrieving tools from MCP servers
    - Managing server status
    """
    
    def __init__(self):
        """Initialize the MCP server manager."""
        self.servers = {}
        self.active_servers = {}
    
    def load_config(self, config_path: str) -> bool:
        """
        Load MCP server configurations from a config file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(config_path):
                logger.error(f"Config file not found: {config_path}")
                return False
                
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if 'mcpServers' not in config:
                logger.error("Invalid config format: 'mcpServers' key not found")
                return False
            
            # Clear existing servers
            self.servers = {}
            
            # Load server configurations
            for server_id, server_config in config['mcpServers'].items():
                if server_config.get('disabled', False):
                    logger.info(f"Skipping disabled server: {server_id}")
                    continue
                    
                command = server_config.get('command')
                args = server_config.get('args', [])
                env = server_config.get('env', {})
                auto_approve = server_config.get('autoApprove', [])
                
                if not command:
                    logger.error(f"Invalid server config for {server_id}: 'command' is required")
                    continue
                
                self.servers[server_id] = {
                    'type': 'stdio',  # Currently only supporting stdio
                    'command': command,
                    'args': args,
                    'env': env,
                    'auto_approve': auto_approve,
                    'description': server_config.get('description', ''),  # Save description
                    'server': None
                }
                
                logger.info(f"Loaded server configuration: {server_id}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return False
    
    def connect_server(self, server_id: str) -> bool:
        """
        Connect to an MCP server.
        
        Args:
            server_id: Identifier of the server to connect to
            
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if server_id not in self.servers:
            logger.error(f"Server {server_id} not found")
            return False
        
        if server_id in self.active_servers:
            logger.warning(f"Server {server_id} is already connected")
            return True
        
        server_config = self.servers[server_id]
        
        try:
            # Currently only supporting stdio servers
            if server_config['type'] == 'stdio':
                params = StdioServerParameters(
                    command=server_config['command'],
                    args=server_config['args'],
                    env=server_config['env']
                )
                
                # Create an MCP client with stdio transport
                from mcp import stdio_client
                server = MCPClient(lambda: stdio_client(params))
                
                # Start the server
                server.start()
                
                # Store the active server
                self.active_servers[server_id] = server
                self.servers[server_id]['server'] = server
                
                logger.info(f"Connected to server: {server_id}")
                return True
            else:
                logger.error(f"Unsupported server type: {server_config['type']}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to server {server_id}: {str(e)}")
            return False
    
    def disconnect_server(self, server_id: str) -> bool:
        """
        Disconnect from an MCP server.
        
        Args:
            server_id: Identifier of the server to disconnect from
            
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        if server_id not in self.active_servers:
            logger.warning(f"Server {server_id} not active or already disconnected")
            return False
        
        try:
            server = self.active_servers[server_id]
            server.stop(None, None, None)
            del self.active_servers[server_id]
            self.servers[server_id]['server'] = None
            logger.info(f"Disconnected from server: {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from server {server_id}: {str(e)}")
            return False
    
    def get_tools(self, server_id: str) -> List[AgentTool]:
        """
        Get tools from an MCP server.
        
        Args:
            server_id: Identifier of the server to get tools from
            
        Returns:
            List[AgentTool]: List of tools provided by the server
        """
        if server_id not in self.active_servers:
            logger.error(f"Server {server_id} not active")
            return []
        
        try:
            server = self.active_servers[server_id]
            tools = server.list_tools_sync()
            logger.info(f"Retrieved {len(tools)} tools from server: {server_id}")
            return tools
        except Exception as e:
            logger.error(f"Failed to get tools from server {server_id}: {str(e)}")
            return []
    
    def get_all_tools(self) -> List[AgentTool]:
        """
        Get tools from all active MCP servers.
        
        Returns:
            List[AgentTool]: Combined list of tools from all active servers
        """
        all_tools = []
        for server_id in self.active_servers:
            all_tools.extend(self.get_tools(server_id))
        
        logger.info(f"Retrieved {len(all_tools)} tools from all active servers")
        return all_tools
    
    def disconnect_all(self) -> None:
        """Disconnect from all active MCP servers."""
        for server_id in list(self.active_servers.keys()):
            self.disconnect_server(server_id)
        
        logger.info("Disconnected from all servers")
    
    def get_server_ids(self) -> List[str]:
        """
        Get the IDs of all configured servers.
        
        Returns:
            List[str]: List of server IDs
        """
        return list(self.servers.keys())
    
    def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get the status of a server.
        
        Args:
            server_id: Identifier of the server
            
        Returns:
            Dict[str, Any]: Server status information
        """
        if server_id not in self.servers:
            return {'exists': False}
        
        server_config = self.servers[server_id]
        is_connected = server_id in self.active_servers
        
        return {
            'exists': True,
            'connected': is_connected,
            'type': server_config['type'],
            'command': server_config['command'],
            'args': server_config['args'],
            'description': server_config.get('description', '')
        }
    
    def get_server_description(self, server_id: str) -> str:
        """
        Get the description of a server.
        
        Args:
            server_id: Identifier of the server
            
        Returns:
            str: Server description
        """
        if server_id not in self.servers:
            return ""
        
        return self.servers[server_id].get('description', '')
    
    def get_all_server_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all configured servers.
        
        Returns:
            Dict[str, str]: Dictionary mapping server IDs to descriptions
        """
        descriptions = {}
        for server_id, server_config in self.servers.items():
            descriptions[server_id] = server_config.get('description', '')
        return descriptions
