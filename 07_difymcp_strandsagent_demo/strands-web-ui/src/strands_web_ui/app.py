#!/usr/bin/env python3
"""
Strands Agent Streamlit Demo with MCP Integration and Audio Transcription

This example demonstrates how to create a simple chat interface for a Strands agent using Streamlit
with Model Context Protocol (MCP) server integration and MP3 audio transcription capabilities.

Run with:
    streamlit run app.py
"""

import os
import time
import logging
import asyncio
import tempfile
import streamlit as st
from strands import Agent, tool
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager

from strands_web_ui.mcp_server_manager import MCPServerManager
from strands_web_ui.handlers.streamlit_handler import StreamlitHandler
from strands_web_ui.utils.config_loader import load_config, load_mcp_config
from strands_web_ui.utils.tool_loader import load_tools_from_config, get_available_tool_names

# Simple no-op handler for non-streaming mode
class NoOpHandler:
    """A no-operation handler that does nothing with events."""
    def __call__(self, **kwargs):
        pass

# Import audio transcription extensions
try:
    from strands_web_ui.extensions.audio_transcriber import transcribe_audio_file_sync, get_supported_languages
    AUDIO_TRANSCRIPTION_AVAILABLE = True
except ImportError as e:
    AUDIO_TRANSCRIPTION_AVAILABLE = False
    logging.warning(f"Audio transcription not available: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example tools can be defined here if needed

def initialize_agent(config, mcp_manager=None):
    """
    Initialize the Strands agent with the given configuration.
    
    Args:
        config: Agent configuration
        mcp_manager: MCP server manager for additional tools
        
    Returns:
        Agent: Initialized Strands agent
    """
    # Create model based on config
    model_config = config.get("model", {})
    
    # Get streaming preference from config
    enable_streaming = model_config.get("enable_streaming", True)
    
    # Add native thinking parameter if enabled
    additional_request_fields = {}
    agent_config = config.get("agent", {})
    if agent_config.get("enable_native_thinking", False):
        # Get thinking budget from config or use default
        thinking_budget = agent_config.get("thinking_budget", 16000)
        # Get max_tokens from model config or use default (1.5x thinking budget)
        max_tokens = model_config.get("max_tokens", int(thinking_budget * 1.5))
        
        additional_request_fields = {
            "max_tokens": max_tokens,
            "thinking": {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        }
    
    # Try to create model with streaming parameter if supported
    try:
        model = BedrockModel(
            model_id=model_config.get("model_id", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
            region=model_config.get("region", "us-east-1"),
            additional_request_fields=additional_request_fields,
            streaming=enable_streaming  # Try to pass streaming parameter
        )
    except TypeError:
        # If streaming parameter is not supported, fall back to default
        logger.warning("BedrockModel does not support streaming parameter, using default behavior")
        model = BedrockModel(
            model_id=model_config.get("model_id", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
            region=model_config.get("region", "us-east-1"),
            additional_request_fields=additional_request_fields
        )
    
    # Import pre-built tools directly
    from strands_tools import (
        calculator,
        editor,
        environment,
        file_read,
        file_write,
        http_request,
        python_repl,
        shell,
        think,
        workflow  # Add workflow tool here
    )
    
    # Create a list of tools based on configuration
    tools_config = config.get("tools", {})
    enabled_tool_names = tools_config.get("enabled", [])
    
    # Map tool names to actual tool objects
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
        "workflow": workflow  # Add workflow to the map
    }
    
    # Select tools based on configuration
    tools = []  # Start with empty tools list
    for tool_name in enabled_tool_names:
        if tool_name in tool_map:
            tools.append(tool_map[tool_name])
            logger.info(f"Added tool: {tool_name}")
    
    # Get tools from MCP servers if available
    if mcp_manager:
        mcp_tools = mcp_manager.get_all_tools()
        tools.extend(mcp_tools)
    
    # Create conversation manager with window size from config
    conversation_config = config.get("conversation", {})
    window_size = conversation_config.get("window_size", 20)
    conversation_manager = SlidingWindowConversationManager(window_size=window_size)
    
    # Add MCP server descriptions to system prompt if available
    enhanced_system_prompt = agent_config.get("system_prompt", "")
    
    if mcp_manager:
        server_descriptions = mcp_manager.get_all_server_descriptions()
        if server_descriptions:
            enhanced_system_prompt += "\n\nMCP Server Information:\n"
            for server_id, description in server_descriptions.items():
                if description:
                    enhanced_system_prompt += f"- {server_id}: {description}\n"
    
    # Initialize agent with conversation manager
    return Agent(
        model=model,
        system_prompt=enhanced_system_prompt,
        tools=tools,
        max_parallel_tools=agent_config.get("max_parallel_tools", os.cpu_count() or 1),
        record_direct_tool_call=agent_config.get("record_direct_tool_call", True),
        load_tools_from_directory=agent_config.get("hot_reload_tools", True),
        conversation_manager=conversation_manager,
        callback_handler=None  # Will be set per interaction
    )

def extract_response_text(response):
    """
    Extract text from the agent's response object.
    
    Args:
        response: Agent response object
        
    Returns:
        str: Extracted text from the response
    """
    # If it's an AgentResult object
    if hasattr(response, 'message'):
        message = response.message
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
            if isinstance(content, list):
                return ''.join(block.get('text', '') for block in content 
                              if isinstance(block, dict) and 'text' in block)
    
    # Handle dictionary format
    if isinstance(response, dict):
        if 'message' in response:
            message = response['message']
            if isinstance(message, dict) and 'content' in message:
                content = message['content']
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        return content[0]['text']
        elif 'final_message' in response:
            final_message = response['final_message']
            if isinstance(final_message, dict) and 'content' in final_message:
                content_blocks = final_message['content']
                return ''.join(block.get('text', '') for block in content_blocks 
                              if isinstance(block, dict) and 'text' in block)
    
    # If we have a get_message_as_string method, use it
    if hasattr(response, 'get_message_as_string'):
        return response.get_message_as_string()
    
    # Fallback
    return str(response)

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Strands Agent Chat with MCP Integration",
        page_icon="🤖",
        layout="wide"
    )
    
    # Add custom CSS for better UI
    st.markdown("""
    <style>
    .media-upload-btn {
        background-color: #f0f2f6;
        border: 2px dashed #cccccc;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .media-upload-btn:hover {
        border-color: #4CAF50;
        background-color: #f8fff8;
    }
    .attachment-info {
        background-color: #e8f4fd;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .transcription-result {
        background-color: #f0f8ff;
        border: 1px solid #b3d9ff;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .step-indicator {
        color: #666;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Load configuration
    initial_config = load_config()
    
    # Initialize MCP server manager
    if "mcp_manager" not in st.session_state:
        st.session_state.mcp_manager = MCPServerManager()
        # Load MCP server configurations
        st.session_state.mcp_manager.load_config("config/mcp_config.json")
    
    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "config" not in st.session_state:
        st.session_state.config = initial_config
    
    if "agent" not in st.session_state:
        st.session_state.agent = initialize_agent(st.session_state.config, st.session_state.mcp_manager)
        
    if "processing" not in st.session_state:
        st.session_state.processing = False
        
    if "thinking_history" not in st.session_state:
        st.session_state.thinking_history = []
    
    # Use session state config for UI controls
    config = st.session_state.config
    
    st.title("🤖 Strands Agent Chat with MCP Integration")
    st.markdown("""
    This demo showcases a Strands agent with streaming responses, tool execution, and MCP server integration.
    You can connect to MCP servers to extend the agent's capabilities with additional tools.
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Agent Configuration")
        
        system_prompt = st.text_area(
            "System Prompt",
            value=config["agent"]["system_prompt"],
            height=100
        )
        
        # Add region selection
        region = st.selectbox(
            "AWS Region",
            options=["us-east-1", "us-west-2", "eu-central-1", "ap-southeast-1"],
            index=0
        )
        
        # Add model selection
        model_id = st.selectbox(
            "Model",
            options=[
                "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
                "us.anthropic.claude-3-5-haiku-20241022-v1:0",
                "us.amazon.nova-premier-v1:0",
                "us.amazon.nova-lite-v1:0",
                "us.amazon.nova-pro-v1:0",
                "us.meta.llama4-maverick-17b-instruct-v1:0",
                "us.meta.llama4-scout-17b-instruct-v1:0"
            ],
            index=0
        )
        
        # Add native thinking toggle
        enable_native_thinking = st.checkbox(
            "Enable Native Thinking",
            value=config["agent"].get("enable_native_thinking", True)
        )
        
        # Add streaming toggle
        enable_streaming = st.checkbox(
            "Enable Streaming Responses",
            value=config["model"].get("enable_streaming", True),
            help="Enable real-time streaming of responses"
        )
        
        # Add conversation window size slider
        window_size = st.slider(
            "Conversation Window Size",
            min_value=5,
            max_value=50,
            value=config["conversation"].get("window_size", 20),
            step=1,
            help="Maximum number of messages to keep in conversation history"
        )
        
        # Tool configuration section
        st.header("Tool Configuration")
        
        # Get all available tool names
        available_tool_names = get_available_tool_names()
        
        # Get currently enabled tools
        enabled_tools = config.get("tools", {}).get("enabled", [])
        
        # Filter enabled tools to only include available ones
        valid_enabled_tools = [tool for tool in enabled_tools if tool in available_tool_names]
        
        # Create multiselect for tool selection
        selected_tools = st.multiselect(
            "Enabled Tools",
            options=available_tool_names,
            default=valid_enabled_tools,  # Use only valid tools as default
            help="Select the tools you want to enable"
        )
        
        if st.button("Apply Configuration"):
            # Update config
            config["model"]["region"] = region
            config["model"]["model_id"] = model_id
            config["model"]["enable_streaming"] = enable_streaming
            config["agent"]["system_prompt"] = system_prompt
            config["agent"]["enable_native_thinking"] = enable_native_thinking
            config["conversation"]["window_size"] = window_size
            
            # Update tools configuration
            if "tools" not in config:
                config["tools"] = {}
            config["tools"]["enabled"] = selected_tools
            
            # Update session state
            st.session_state.config = config
            st.session_state.agent = initialize_agent(config, st.session_state.mcp_manager)
            st.success("Configuration applied!")
        
        st.divider()
        
        # MCP Server Configuration
        st.header("MCP Server Configuration")
        
        # Display configured servers
        mcp_manager = st.session_state.mcp_manager
        server_ids = mcp_manager.get_server_ids()
        
        if server_ids:
            for server_id in server_ids:
                status = mcp_manager.get_server_status(server_id)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if status.get('connected', False):
                        st.write(f"✅ {server_id}")
                    else:
                        st.write(f"⚪ {server_id}")
                
                with col2:
                    if status.get('connected', False):
                        if st.button(f"Disconnect", key=f"disconnect_{server_id}"):
                            if mcp_manager.disconnect_server(server_id):
                                st.success(f"Disconnected from {server_id}")
                                # Reinitialize agent with updated tools
                                st.session_state.agent = initialize_agent(
                                    st.session_state.config, 
                                    mcp_manager
                                )
                            else:
                                st.error(f"Failed to disconnect from {server_id}")
                    else:
                        if st.button(f"Connect", key=f"connect_{server_id}"):
                            if mcp_manager.connect_server(server_id):
                                st.success(f"Connected to {server_id}")
                                # Reinitialize agent with new tools
                                st.session_state.agent = initialize_agent(
                                    st.session_state.config, 
                                    mcp_manager
                                )
                            else:
                                st.error(f"Failed to connect to {server_id}")
                
                # Display server details
                with st.expander(f"Server details: {server_id}"):
                    st.write(f"Command: {status.get('command', 'N/A')}")
                    st.write(f"Args: {', '.join(status.get('args', []))}")
                    st.write(f"Status: {'Connected' if status.get('connected', False) else 'Disconnected'}")
        else:
            st.info("No MCP servers configured. Edit the mcp_config.json file to add servers.")
        
        # Reload configuration button
        if st.button("Reload MCP Configuration"):
            if mcp_manager.load_config("config/mcp_config.json"):
                st.success("MCP configuration reloaded")
            else:
                st.error("Failed to reload MCP configuration")
        
        # Display active tools
        st.header("Active Tools")
        
        # Get SDK tools from config
        sdk_tools = config.get("tools", {}).get("enabled", [])
        if sdk_tools:
            st.subheader("SDK Tools")
            for tool_name in sdk_tools:
                st.write(f"- {tool_name}")
        
        # Get MCP tools
        mcp_tools = []
        for server_id in server_ids:
            status = mcp_manager.get_server_status(server_id)
            if status.get('connected', False):
                server_tools = mcp_manager.get_tools(server_id)
                if server_tools:
                    if not mcp_tools:  # Only add header if we have tools
                        st.subheader("MCP Tools")
                    for tool in server_tools:
                        tool_name = getattr(tool, "__name__", str(tool))
                        st.write(f"- {tool_name} ({server_id})")
    
    # Display conversation history with thinking processes
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If this is an assistant message, check if there's thinking history for the previous question
            if message["role"] == "assistant" and i > 0:  # Make sure there's a previous message
                # Find thinking content for the previous question (user message)
                for thinking_item in st.session_state.thinking_history:
                    if thinking_item["question_idx"] == i-1:  # i-1 is the index of the user message
                        # Display the thinking content
                        with st.expander("💭 Thinking Process", expanded=False):
                            st.markdown(f"""
                            <div style="background-color: rgba(67, 97, 238, 0.1); padding: 10px; border-left: 4px solid #4361ee; border-radius: 4px; color: var(--text-color, currentColor);">
                            {thinking_item["content"]}
                            </div>
                            """, unsafe_allow_html=True)
                        break
    
    # Initialize session state for media upload
    if "uploaded_audio_file" not in st.session_state:
        st.session_state.uploaded_audio_file = None
    if "audio_file_name" not in st.session_state:
        st.session_state.audio_file_name = None
    if "show_media_upload" not in st.session_state:
        st.session_state.show_media_upload = False
    
    # Show attached file info if exists
    if st.session_state.uploaded_audio_file is not None:
        st.markdown(f"""
        <div class="attachment-info">
            📎 <strong>Attached:</strong> {st.session_state.audio_file_name}
            <br><small>This audio file will be transcribed and included with your next message</small>
        </div>
        """, unsafe_allow_html=True)
        
        col_remove, col_change = st.columns([1, 1])
        with col_remove:
            if st.button("🗑️ Remove", key="remove_attachment"):
                st.session_state.uploaded_audio_file = None
                st.session_state.audio_file_name = None
                st.rerun()
        with col_change:
            if st.button("📎 Change File", key="change_attachment"):
                st.session_state.show_media_upload = True
    
    # Media upload section
    if not st.session_state.uploaded_audio_file or st.session_state.show_media_upload:
        # Media upload button
        if not st.session_state.show_media_upload:
            if st.button("📎 Attach Audio File", help="Upload MP3 or WAV file for transcription", key="media_upload_btn"):
                st.session_state.show_media_upload = True
                st.rerun()
    
    # Show media upload dialog if button was clicked
    if st.session_state.show_media_upload:
        with st.container():
            st.markdown("### 📎 Attach Audio File")
            
            uploaded_file = st.file_uploader(
                "Choose an MP3 or WAV file to transcribe",
                type=['mp3', 'wav'],
                help="Upload an MP3 or WAV audio file. It will be transcribed and combined with your text message.",
                key="audio_uploader"
            )
            
            if uploaded_file is not None:
                # Show file info
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.info(f"📁 **File:** {uploaded_file.name} ({file_size_mb:.1f} MB)")
                
                # Configuration options
                col_lang, col_region = st.columns(2)
                with col_lang:
                    language_options = st.multiselect(
                        "🌍 Language Detection",
                        options=["en-US", "id-ID", "zh-CN", "ja-JP", "ko-KR", "th-TH"],
                        default=["en-US", "id-ID"],
                        help="Select languages for automatic detection"
                    )
                
                with col_region:
                    aws_region = st.selectbox(
                        "🌐 AWS Region",
                        options=["ap-southeast-1", "us-east-1", "us-west-2", "eu-central-1"],
                        index=0,
                        help="AWS region for Transcribe service"
                    )
                
                # Action buttons
                col_attach, col_cancel = st.columns(2)
                with col_attach:
                    if st.button("✅ Attach File", type="primary", key="confirm_attach"):
                        st.session_state.uploaded_audio_file = uploaded_file.getvalue()
                        st.session_state.audio_file_name = uploaded_file.name
                        st.session_state.audio_language_options = language_options
                        st.session_state.audio_aws_region = aws_region
                        st.session_state.show_media_upload = False
                        st.success(f"📎 Attached: {uploaded_file.name}")
                        time.sleep(1)  # Brief pause to show success message
                        st.rerun()
                
                with col_cancel:
                    if st.button("❌ Cancel", key="cancel_attach"):
                        st.session_state.show_media_upload = False
                        st.rerun()
            else:
                # Cancel button when no file selected
                if st.button("❌ Cancel", key="cancel_no_file"):
                    st.session_state.show_media_upload = False
                    st.rerun()
    
    # Get user input
    user_input = st.chat_input("Ask something...", disabled=st.session_state.processing)
    
    if user_input:
        # Set processing flag to prevent multiple submissions
        st.session_state.processing = True
        
        # Check if there's an audio file attached
        has_audio_attachment = st.session_state.uploaded_audio_file is not None
        final_input = user_input
        
        # Display user message first
        with st.chat_message("user"):
            if has_audio_attachment:
                st.markdown(f"📎 **Attached:** {st.session_state.audio_file_name}")
            st.markdown(user_input)
        
        # Add user message to chat history
        display_message = user_input
        if has_audio_attachment:
            display_message = f"📎 {st.session_state.audio_file_name}\n\n{user_input}"
        st.session_state.messages.append({"role": "user", "content": display_message})
        
        # Create a placeholder for the streaming response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            try:
                # Step 1: Process audio if attached
                if has_audio_attachment and AUDIO_TRANSCRIPTION_AVAILABLE:
                    # Show transcription progress
                    response_placeholder.markdown("🎤 **Step 1/2:** Transcribing audio...")
                    
                    # Save audio file temporarily
                    # Determine file extension from the original filename
                    file_extension = st.session_state.audio_file_name.lower().split('.')[-1]
                    if file_extension not in ['mp3', 'wav']:
                        file_extension = 'mp3'  # Default fallback
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                        tmp_file.write(st.session_state.uploaded_audio_file)
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Transcribe audio
                        transcription_result = transcribe_audio_file_sync(
                            file_path=tmp_file_path,
                            language_options=st.session_state.get("audio_language_options", ["en-US", "id-ID"]),
                            region=st.session_state.get("audio_aws_region", "ap-southeast-1")
                        )
                        
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
                        
                        if transcription_result["status"] == "success":
                            transcript = transcription_result["transcript"]
                            detected_language = transcription_result["language_code"]
                            confidence = transcription_result.get("confidence")
                            
                            # Show transcription result with better formatting
                            transcription_display = f"""
<div class="transcription-result">
<div class="step-indicator">🎤 Step 1/2: Audio Transcription Completed</div>

<strong>📋 Transcription Results:</strong>
<ul>
<li><strong>Language Detected:</strong> {detected_language or 'Unknown'}</li>
<li><strong>Confidence:</strong> {f'{confidence:.1%}' if confidence else 'N/A'}</li>
<li><strong>File:</strong> {st.session_state.audio_file_name}</li>
</ul>

<strong>📝 Transcript:</strong>
<div style="background-color: white; padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 4px solid #4CAF50;">
<em>"{transcript}"</em>
</div>

<div class="step-indicator">🤖 Step 2/2: Processing with AI Agent...</div>
</div>
"""
                            response_placeholder.markdown(transcription_display, unsafe_allow_html=True)
                            
                            # Combine transcript with user input
                            final_input = f"""User Request: {user_input}

Audio Transcription (Language: {detected_language}):
{transcript}"""
                            
                            # Clear audio attachment after use
                            st.session_state.uploaded_audio_file = None
                            st.session_state.audio_file_name = None
                            
                        else:
                            # Transcription failed, show error and continue with text only
                            error_msg = f"""
<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 10px 0;">
⚠️ <strong>Audio transcription failed:</strong> {transcription_result['message']}
<br><br>
<em>Continuing with text input only...</em>
</div>
"""
                            response_placeholder.markdown(error_msg, unsafe_allow_html=True)
                            time.sleep(3)  # Show error for 3 seconds
                            
                    except Exception as e:
                        # Handle transcription errors
                        error_msg = f"""
<div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; padding: 15px; margin: 10px 0;">
❌ <strong>Audio processing error:</strong> {str(e)}
<br><br>
<em>Continuing with text input only...</em>
</div>
"""
                        response_placeholder.markdown(error_msg, unsafe_allow_html=True)
                        time.sleep(3)  # Show error for 3 seconds
                        
                        # Clean up temporary file if it exists
                        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
                
                # Step 2: Process with agent
                # Check streaming config
                streaming_enabled = st.session_state.config["model"].get("enable_streaming", True)
                
                # Debug logging
                print("\n===== INTEGRATED AUDIO + TEXT PROCESSING =====")
                print(f"Original user input: {user_input}")
                print(f"Has audio attachment: {has_audio_attachment}")
                print(f"Final input to agent: {final_input}")
                print(f"Streaming enabled: {streaming_enabled}")
                print("=" * 50)
                
                # Use the existing agent instance from session state
                agent = st.session_state.agent
                
                if streaming_enabled:
                    # Streaming mode (existing behavior)
                    ui_config = st.session_state.config.get("ui", {})
                    update_interval = ui_config.get("update_interval", 0.1)
                    
                    stream_handler = StreamlitHandler(
                        placeholder=response_placeholder,
                        update_interval=update_interval
                    )
                    
                    agent.callback_handler = stream_handler
                    
                    # Process with streaming
                    response = agent(final_input)
                    response_text = extract_response_text(response)
                    
                    # Handle streaming response display
                    if not stream_handler.message_container:
                        response_placeholder.markdown(response_text)
                    else:
                        response_placeholder.markdown(stream_handler.message_container)
                    
                    # Make sure thinking content is preserved after the response
                    if stream_handler.thinking_container and not stream_handler.thinking_preserved:
                        stream_handler._preserve_thinking_content()
                    
                    final_response_text = response_text or stream_handler.message_container
                    
                else:
                    # Non-streaming mode
                    with st.spinner("Processing your request..."):
                        agent.callback_handler = NoOpHandler()  # Use no-op handler instead of None
                        
                        # Process without streaming
                        response = agent(final_input)
                        response_text = extract_response_text(response)
                        
                        # Display complete response at once
                        response_placeholder.markdown(response_text)
                        final_response_text = response_text
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": final_response_text})
                
            except Exception as e:
                # Handle errors gracefully
                error_message = f"Error: {str(e)}"
                print(f"ERROR in agent execution: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(traceback.format_exc())
                response_placeholder.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            
            finally:
                # Reset processing flag
                st.session_state.processing = False

if __name__ == "__main__":
    main()
