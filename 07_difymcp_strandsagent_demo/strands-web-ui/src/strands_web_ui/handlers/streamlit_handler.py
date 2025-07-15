"""
Streamlit handler for Strands agents.

This module provides a callback handler for Strands agents that updates a Streamlit UI
with streaming responses, thinking process visualization, and tool execution.
"""

import time
import logging
import streamlit as st
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StreamlitHandler:
    """
    Callback handler for Strands agents that updates a Streamlit UI.
    
    This handler supports:
    - Streaming text responses
    - Visualizing the agent's thinking process
    - Displaying tool execution and results
    
    Attributes:
        placeholder: Streamlit placeholder for displaying content
        update_interval: Time between UI updates (seconds)
    """
    
    def __init__(self, placeholder, update_interval=0.1):
        """
        Initialize the Streamlit handler.
        
        Args:
            placeholder: Streamlit placeholder for displaying content
            update_interval: Time between UI updates (seconds)
        """
        self.placeholder = placeholder
        self.message_container = ""
        self.thinking_container = ""
        self.is_thinking = False
        self.last_update_time = time.time()
        self.update_interval = update_interval
        self.tool_containers = {}
        self.thinking_placeholder = None
        # Add a flag to track if thinking content has been preserved
        self.thinking_preserved = False
        # Store the thinking content in session state to persist across rerenders
        if "thinking_content" not in st.session_state:
            st.session_state.thinking_content = ""
        
        # Add buffers for collecting complete messages
        self.current_reasoning = ""
        self.current_message = ""
        self.delta_buffer = ""
        self.current_tool_calls = {}  # Track tool calls by ID
        self.current_tool_results = {}  # Track tool results by ID
        
    def __call__(self, **kwargs):
        """
        Process events from the Strands agent with enhanced ReAct context logging.
        
        Args:
            **kwargs: Event data from the agent
        """
        # Get event type
        event_type = next((k for k in kwargs.keys() if k not in ["data", "content_block_delta"]), None)
        
        # Handle initialization - reset buffers
        if "init_event_loop" in kwargs:
            print("[ReAct - START] New interaction started")
            self.current_reasoning = ""
            self.current_message = ""
            self.delta_buffer = ""
            self.current_tool_calls = {}
            self.current_tool_results = {}
            self._handle_initialization()
            return
            
        # Handle reasoning text - collect complete reasoning
        if event_type == "reasoningText":
            reasoning_text = kwargs.get("reasoningText", "")
            if isinstance(reasoning_text, dict) and "text" in reasoning_text:
                reasoning_text = reasoning_text["text"]
            self.current_reasoning += str(reasoning_text)
            
        # When reasoning is complete, output the full reasoning
        elif event_type == "reasoning_signature":
            if self.current_reasoning:
                print(f"[ReAct - REASONING COMPLETE]\n{self.current_reasoning}")
                self.current_reasoning = ""  # Reset after printing
                
        # Handle delta events - collect content but don't print every delta
        elif event_type == "delta":
            delta_content = kwargs.get("delta", {}).get("text", "")
            if delta_content:
                self.delta_buffer += delta_content
                
        # Handle message events - output complete messages
        elif event_type == "message":
            message = kwargs.get("message", {})
            if isinstance(message, dict) and "content" in message:
                content = message["content"]
                full_text = ""
                
                # Extract text from content blocks
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if "text" in block:
                                full_text += block["text"]
                            elif "toolUse" in block:
                                tool_use = block["toolUse"]
                                tool_id = tool_use.get("toolUseId", "unknown")
                                self.current_tool_calls[tool_id] = tool_use
                                print(f"[ReAct - ACTION] Tool: {tool_use.get('name')}, Input: {tool_use.get('input')}")
                            elif "toolResult" in block:
                                tool_result = block["toolResult"]
                                tool_id = tool_result.get("toolUseId", "unknown")
                                self.current_tool_results[tool_id] = tool_result
                                print(f"[ReAct - OBSERVATION] Tool: {tool_id}, Status: {tool_result.get('status')}")
                                if "content" in tool_result:
                                    print(f"[ReAct - OBSERVATION CONTENT] {tool_result['content']}")
                
                # Print the complete message if it's not empty
                if full_text:
                    print(f"[COMPLETE MESSAGE]\n{full_text}")
                    
                # Also print any buffered delta content if it wasn't part of a message
                if self.delta_buffer:
                    print(f"[COMPLETE DELTA CONTENT]\n{self.delta_buffer}")
                    self.delta_buffer = ""  # Reset buffer
                    
        # Handle direct tool events
        elif "tool_use" in kwargs:
            tool_use = kwargs["tool_use"]
            tool_id = tool_use.get("toolUseId", "unknown")
            self.current_tool_calls[tool_id] = tool_use
            print(f"[ReAct - ACTION DIRECT] Tool: {tool_use.get('name')}, Input: {tool_use.get('input')}")
            
        elif "tool_result" in kwargs:
            tool_result = kwargs["tool_result"]
            tool_id = tool_result.get("toolUseId", "unknown")
            self.current_tool_results[tool_id] = tool_result
            print(f"[ReAct - OBSERVATION DIRECT] Status: {tool_result.get('status')}")
            if "content" in tool_result:
                print(f"[ReAct - OBSERVATION CONTENT] {tool_result['content']}")
                
        # Handle event with potential MCP tool information
        elif event_type == "event":
            # Check for MCP tool information in various locations
            if "current_tool_use" in kwargs:
                tool = kwargs["current_tool_use"]
                tool_id = tool.get("toolUseId", "unknown")
                self.current_tool_calls[tool_id] = tool
                print(f"[ReAct - ACTION MCP] Tool: {tool.get('name')}, Input: {tool.get('input')}")
                
            # Check for tool information in content
            elif "content" in kwargs:
                content = kwargs["content"]
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if "toolUse" in item:
                                tool_use = item["toolUse"]
                                tool_id = tool_use.get("toolUseId", "unknown")
                                self.current_tool_calls[tool_id] = tool_use
                                print(f"[ReAct - ACTION MCP] Tool: {tool_use.get('name')}, Input: {tool_use.get('input')}")
                            elif "toolResult" in item:
                                tool_result = item["toolResult"]
                                tool_id = tool_result.get("toolUseId", "unknown")
                                self.current_tool_results[tool_id] = tool_result
                                print(f"[ReAct - OBSERVATION MCP] Tool: {tool_id}, Status: {tool_result.get('status')}")
                                if "content" in tool_result:
                                    print(f"[ReAct - OBSERVATION CONTENT] {tool_result['content']}")
            
            # For debugging - print full event data for unhandled events
            # Uncomment this for debugging if needed
            # else:
            #     print(f"[DEBUG] Unhandled event data: {kwargs}")
        
        # Continue with the original handler logic for UI updates
        if "init_event_loop" in kwargs:
            self._handle_initialization()
            return
        
        # Handle thinking events - now handling reasoningText and reasoning_signature
        if "reasoningText" in kwargs:
            # This is the thinking content we need to capture
            self._handle_thinking_content(kwargs["reasoningText"])
            return
            
        if "reasoning_signature" in kwargs:
            # This marks the end of the thinking process
            self._handle_thinking_end()
            return
            
        # Original thinking events (keeping for backward compatibility)
        if "thinking_start" in kwargs:
            self._handle_thinking_start()
            return
            
        if "thinking" in kwargs:
            self._handle_thinking(kwargs["thinking"])
            return
            
        if "thinking_end" in kwargs:
            self._handle_thinking_end()
            return
            
        # Handle text streaming (both content_block_delta and data paths)
        self._handle_text_streaming(kwargs)
        
        # Handle tool events
        self._handle_tool_events(kwargs)
        
        # Handle final message - ensure thinking content remains visible
        if "message" in kwargs and not self.thinking_preserved:
            # Make sure thinking content is preserved
            self._preserve_thinking_content()
    
    def _handle_initialization(self):
        """Reset state and show thinking indicator."""
        self.message_container = ""
        self.thinking_container = ""
        self.is_thinking = False
        self.last_update_time = time.time()
        self.placeholder.markdown("_Thinking..._")
        # Reset thinking placeholder
        self.thinking_placeholder = None
        # Reset thinking preserved flag
        self.thinking_preserved = False
    
    def _handle_thinking_start(self):
        """Handle the start of a thinking event."""
        self.is_thinking = True
        self.thinking_container = ""
        # Create a thinking expander with a distinctive style
        with self.placeholder.expander("💭 Model Thinking Process", expanded=True):
            self.thinking_placeholder = st.empty()
            # Use a distinctive style for thinking content
            self.thinking_placeholder.markdown("""
            <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px; color: var(--text-color, currentColor);">
            <em>Starting to think...</em>
            </div>
            """, unsafe_allow_html=True)
    
    def _handle_thinking_content(self, reasoning_text):
        """
        Handle reasoning text content.
        
        Args:
            reasoning_text: Reasoning text from the agent
        """
        # Initialize thinking container if this is the first thinking content
        if not self.thinking_container:
            self._handle_thinking_start()
        
        # Extract text from the reasoning text
        if isinstance(reasoning_text, dict) and "text" in reasoning_text:
            thinking_text = reasoning_text["text"]
        elif isinstance(reasoning_text, str):
            thinking_text = reasoning_text
        else:
            # Debug the structure if it's not what we expect
            logger.debug(f"Unexpected reasoningText structure: {reasoning_text}")
            thinking_text = str(reasoning_text)
        
        # Add the thinking text to our container
        self.thinking_container += thinking_text
        
        # Update the thinking placeholder
        current_time = time.time()
        if current_time - self.last_update_time > self.update_interval:
            if self.thinking_placeholder:
                self.thinking_placeholder.markdown(f"""
                <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px; color: var(--text-color, currentColor);">
                {self.thinking_container}
                </div>
                """, unsafe_allow_html=True)
            self.last_update_time = current_time
    
    def _handle_thinking(self, thinking_data):
        """
        Handle thinking content.
        
        Args:
            thinking_data: Thinking data from the agent
        """
        # Extract thinking content from various possible structures
        thinking_text = None
        
        # Handle the reasoningContent structure
        if isinstance(thinking_data, dict) and "reasoningContent" in thinking_data:
            reasoning = thinking_data["reasoningContent"]
            if isinstance(reasoning, dict) and "reasoningText" in reasoning:
                reasoning_text = reasoning["reasoningText"]
                if isinstance(reasoning_text, dict) and "text" in reasoning_text:
                    thinking_text = reasoning_text["text"]
        # Fallback for other formats
        elif isinstance(thinking_data, str):
            thinking_text = thinking_data
        elif isinstance(thinking_data, dict) and "text" in thinking_data:
            thinking_text = thinking_data["text"]
            
        # If we found thinking text, add it to the container with formatting
        if thinking_text:
            # Add formatting to clearly distinguish thinking content
            formatted_thinking = f"💭 {thinking_text}"
            self.thinking_container += formatted_thinking
            # Also store in session state for persistence
            st.session_state.thinking_content = self.thinking_container
            
            # Update the thinking placeholder
            current_time = time.time()
            if current_time - self.last_update_time > self.update_interval:
                if self.thinking_placeholder:
                    self.thinking_placeholder.markdown(self.thinking_container)
                self.last_update_time = current_time
    
    def _handle_thinking_end(self):
        """Handle the end of a thinking event."""
        self.is_thinking = False
        # Ensure the final thinking content is displayed with styling
        if self.thinking_container and self.thinking_placeholder:
            # Keep the original thinking placeholder updated
            self.thinking_placeholder.markdown(f"""
            <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px; color: var(--text-color, currentColor);">
            {self.thinking_container}
            </div>
            <p style="color: var(--text-color, currentColor);"><em>End of thinking process</em></p>
            """, unsafe_allow_html=True)
            
            # Preserve the thinking content in a permanent location
            self._preserve_thinking_content()
    
    def _preserve_thinking_content(self):
        """Ensure thinking content remains visible after the response is complete."""
        if self.thinking_container and not self.thinking_preserved:
            # Mark as preserved so we don't duplicate
            self.thinking_preserved = True
            
            # Store the thinking content in session state for persistence across rerenders
            if len(st.session_state.messages) > 0:  # Make sure there's a message to associate with
                question_idx = len(st.session_state.messages) - 1
                # Store the thinking content with the question index
                st.session_state.thinking_history.append({
                    "question_idx": question_idx,
                    "content": self.thinking_container
                })
                
            # Create a permanent container for the thinking content
            # This will be displayed below the response
            thinking_container = st.container()
            with thinking_container:
                st.markdown("### 💭 Thinking Process")
                st.markdown(f"""
                <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px; color: var(--text-color, currentColor);">
                {self.thinking_container}
                </div>
                <p style="color: var(--text-color, currentColor);"><em>End of thinking process</em></p>
                """, unsafe_allow_html=True)
    
    def _handle_text_streaming(self, kwargs):
        """
        Extract and display streaming text from various event formats.
        
        Args:
            kwargs: Event data from the agent
        """
        text_chunk = None
        
        # Extract text from content_block_delta format
        if "content_block_delta" in kwargs:
            delta = kwargs["content_block_delta"]
            if "delta" in delta and "text" in delta["delta"]:
                text_chunk = delta["delta"]["text"]
        
        # Extract text from data format
        elif "data" in kwargs:
            data = kwargs["data"]
            if isinstance(data, str):
                text_chunk = data
            elif isinstance(data, dict) and "delta" in data:
                delta = data["delta"]
                if isinstance(delta, dict) and "text" in delta:
                    text_chunk = delta["text"]
        
        # Update UI if we found text
        if text_chunk:
            self.message_container += text_chunk
            self._update_ui_if_needed()
    
    def _handle_tool_events(self, kwargs):
        """
        Handle tool use and tool result events.
        
        Args:
            kwargs: Event data from the agent
        """
        # Force update any accumulated text first
        if any(k in kwargs for k in ["tool_use", "tool_result", "content_block_start"]):
            if self.message_container:
                self.placeholder.markdown(self.message_container)
            
            # Handle tool use
            if "tool_use" in kwargs:
                self._handle_tool_use(kwargs["tool_use"])
            
            # Handle tool results
            if "tool_result" in kwargs:
                self._handle_tool_result(kwargs["tool_result"])
    
    def _handle_tool_use(self, tool_use):
        """
        Display tool execution in UI.
        
        Args:
            tool_use: Tool use data from the agent
        """
        tool_id = tool_use["toolUseId"]
        tool_name = tool_use["name"]
        
        # Create a container for this tool
        tool_container = st.container()
        self.tool_containers[tool_id] = tool_container
        
        # Show tool execution in UI
        with tool_container:
            st.info(f"🔧 Using tool: **{tool_name}**")
            st.json(tool_use.get("input", {}))
    
    def _handle_tool_result(self, tool_result):
        """
        Display tool result in UI.
        
        Args:
            tool_result: Tool result data from the agent
        """
        tool_id = tool_result["toolUseId"]
        
        # Get the container for this tool or create a new one
        tool_container = self.tool_containers.get(tool_id, st.container())
        
        # Show tool result in UI
        with tool_container:
            if tool_result["status"] == "success":
                st.success(f"✅ Tool completed successfully")
            else:
                st.error(f"❌ Tool failed")
            
            # Display results
            for content in tool_result.get("content", []):
                if "text" in content:
                    st.write(content["text"])
                elif "json" in content:
                    self._visualize_json_content(content["json"])
    
    def _visualize_json_content(self, json_data):
        """
        Visualize JSON content, with special handling for chart data.
        
        Args:
            json_data: JSON data to visualize
        """
        if isinstance(json_data, dict) and "labels" in json_data and "values" in json_data:
            chart_data = {"x": json_data["labels"], "y": json_data["values"]}
            st.bar_chart(chart_data)
        else:
            st.json(json_data)
    
    def _update_ui_if_needed(self):
        """Update the UI if enough time has passed since the last update."""
        current_time = time.time()
        if current_time - self.last_update_time > self.update_interval:
            self.placeholder.markdown(self.message_container)
            self.last_update_time = current_time
